"""Boardroom OS MVP. Run: uvicorn app:app --reload"""
import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agents import BY_ID, public_agents, select_participants
from engine import MissingKeyError, ask_agent, configured, opening_round, debate_round, MODEL

BASE = Path(__file__).parent
DB_PATH = Path(os.environ.get("BOARDROOM_DB_PATH", str(BASE / "boardroom.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
write_lock = Lock()
app = FastAPI(title="Boardroom OS", version="0.1.0")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, agenda TEXT NOT NULL,
            context TEXT NOT NULL DEFAULT '', participants TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open', decision TEXT,
            decision_rationale TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, meeting_id TEXT NOT NULL,
            speaker_id TEXT NOT NULL, speaker_name TEXT NOT NULL, content TEXT NOT NULL,
            mode TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id)
        );
        CREATE INDEX IF NOT EXISTS ix_messages_meeting ON messages(meeting_id, id);
        """)


init_db()


class CreateMeeting(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    agenda: str = Field(min_length=5, max_length=3000)
    context: str = Field(default="", max_length=12000)


class DirectQuestion(BaseModel):
    agent_id: str
    question: str = Field(min_length=3, max_length=4000)


class DecisionBody(BaseModel):
    decision: str = Field(min_length=3, max_length=4000)
    rationale: str = Field(default="", max_length=4000)


def get_meeting(meeting_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Meeting not found")
        result = dict(row)
        result["participants"] = json.loads(result["participants"])
        result["messages"] = [dict(m) for m in db.execute("SELECT * FROM messages WHERE meeting_id = ? ORDER BY id", (meeting_id,))]
        return result


def require_open(meeting_id):
    meeting = get_meeting(meeting_id)
    if meeting["status"] != "open":
        raise HTTPException(409, "This meeting has been closed. Create a new meeting to continue.")
    return meeting


def require_ai():
    if not configured():
        raise HTTPException(503, "Live AI is not configured. Set OPENAI_API_KEY in the server environment, restart, and try again. The in-browser demo remains available.")


def save_messages(meeting_id: str, generated: list[tuple[str, str]], mode: str):
    ts = now()
    with write_lock:
        with connect() as db:
            for speaker, content in generated:
                db.execute("INSERT INTO messages (meeting_id, speaker_id, speaker_name, content, mode, created_at) VALUES (?,?,?,?,?,?)",
                           (meeting_id, speaker, BY_ID[speaker].name if speaker in BY_ID else "Chairperson", content, mode, ts))
            db.execute("UPDATE meetings SET updated_at = ? WHERE id = ?", (ts, meeting_id))
    return get_meeting(meeting_id)


async def execute(coro):
    try:
        return await coro
    except MissingKeyError as e:
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        # Do not leak internal tokens, credentials, or API error objects to users.
        print(f"Boardroom engine error: {type(e).__name__}")
        raise HTTPException(502, "The AI provider could not complete this boardroom round. Check server logs and try again.") from e


@app.get("/api/health")
def health():
    return {"status": "ok", "live_ai": configured(), "model": MODEL}


@app.get("/api/agents")
def agents():
    return public_agents()


@app.get("/api/meetings")
def list_meetings():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT id, title, agenda, status, created_at, updated_at FROM meetings ORDER BY created_at DESC LIMIT 30")]


@app.post("/api/meetings", status_code=201)
def create_meeting(data: CreateMeeting):
    meeting_id = str(uuid.uuid4())
    ts = now()
    participants = select_participants(data.agenda + " " + data.context)
    with write_lock:
        with connect() as db:
            db.execute("INSERT INTO meetings(id,title,agenda,context,participants,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                       (meeting_id, data.title.strip(), data.agenda.strip(), data.context.strip(), json.dumps(participants), ts, ts))
    return get_meeting(meeting_id)


@app.get("/api/meetings/{meeting_id}")
def read_meeting(meeting_id: str):
    return get_meeting(meeting_id)


@app.post("/api/meetings/{meeting_id}/opening")
async def open_discussion(meeting_id: str):
    meeting = require_open(meeting_id)
    require_ai()
    if meeting["messages"]:
        raise HTTPException(409, "The opening round has already occurred.")
    generated = await execute(opening_round(meeting["agenda"], meeting["context"], meeting["participants"]))
    return save_messages(meeting_id, generated, "opening")


@app.post("/api/meetings/{meeting_id}/debate")
async def debate(meeting_id: str):
    meeting = require_open(meeting_id)
    require_ai()
    if not meeting["messages"]:
        raise HTTPException(409, "Run the opening round before a debate.")
    # Two directly contrasting perspectives plus the independent challenger.
    active = [a for a in meeting["participants"] if a != "devil"][:2] + ["devil"]
    generated = await execute(debate_round(meeting["agenda"], meeting["context"], meeting["messages"], active))
    return save_messages(meeting_id, generated, "debate")


@app.post("/api/meetings/{meeting_id}/ask")
async def ask(meeting_id: str, data: DirectQuestion):
    meeting = require_open(meeting_id)
    require_ai()
    if data.agent_id not in BY_ID:
        raise HTTPException(400, "Unknown board member")
    # Chair's own question becomes part of the history and is persisted ONLY once the model call succeeds.
    history = meeting["messages"] + [{"speaker_name": "Chairperson", "content": data.question}]
    content = await execute(ask_agent(data.agent_id, meeting["agenda"], meeting["context"], history, data.question, "question"))
    return save_messages(meeting_id, [("chair", data.question), (data.agent_id, content)], "question")


@app.post("/api/meetings/{meeting_id}/summary")
async def summary(meeting_id: str):
    meeting = require_open(meeting_id)
    require_ai()
    if not meeting["messages"]:
        raise HTTPException(409, "Get at least one expert assessment before a summary.")
    content = await execute(ask_agent("chief", meeting["agenda"], meeting["context"], meeting["messages"],
                                      "Summarize the board recommendation, strongest opposing argument, missing data, and decision options. Do NOT declare a decision approved.", "summary"))
    return save_messages(meeting_id, [("chief", content)], "summary")


@app.post("/api/meetings/{meeting_id}/decision")
def approve_decision(meeting_id: str, data: DecisionBody):
    require_open(meeting_id)
    ts = now()
    with write_lock:
        with connect() as db:
            db.execute("UPDATE meetings SET decision = ?, decision_rationale = ?, status = 'closed', updated_at = ? WHERE id = ?",
                       (data.decision.strip(), data.rationale.strip(), ts, meeting_id))
    return get_meeting(meeting_id)


@app.get("/api/meetings/{meeting_id}/export", response_class=PlainTextResponse)
def export_minutes(meeting_id: str):
    meeting = get_meeting(meeting_id)
    parts = [f"# {meeting['title']}", f"Date: {meeting['created_at']}", f"Agenda: {meeting['agenda']}",
             f"Context: {meeting['context']}", "", "## Meeting Transcript"]
    for m in meeting["messages"]:
        parts.append(f"\n**{m['speaker_name']}** ({m['mode']})\n{m['content']}")
    parts += ["", "## Chairperson Decision", meeting["decision"] or "Not decided",
              "", "## Rationale", meeting["decision_rationale"] or "Not recorded"]
    return PlainTextResponse("\n".join(parts), headers={"Content-Disposition": f'attachment; filename="boardroom-{meeting_id[:8]}.md"'})


app.mount("/static", StaticFiles(directory=str(BASE / "web")), name="static")


@app.get("/")
def homepage():
    return FileResponse(BASE / "web" / "index.html")
