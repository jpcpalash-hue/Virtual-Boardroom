# Boardroom OS — Chairperson POV AI Boardroom (MVP)

A runnable local prototype: an illustrated first-person boardroom, named AI advisors, independent expert calls, structured debate, direct questioning, a chair-only decision gate, and SQLite meeting records.

**This is a 2.5D SVG boardroom prototype, not photorealistic 3D.** The visual demo is **scripted**, clearly labeled as such. Live meetings invoke the OpenAI API separately for each expert. No live model responses are available until you provide a valid OpenAI API key.

## Instant offline visual demo

Open the separate `Boardroom_OS_Interactive_Demo.html` in your browser to explore the scripted visual meeting without running Python. It does not connect to a backend or answer new questions.

## Quick start

Requirements: Python 3.10+.

```bash
cd boardroom_os_mvp
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

To try the interface **without an API key**, run:

```bash
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000**. The preloaded sample discussion and avatars work without API access, but its lines are prewritten and do not answer new questions.

To activate **real AI specialists**, set your API key in the server environment (never browser JS):

```bash
# macOS/Linux
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-5.6-terra"    # optional; configure a model your account can access
uvicorn app:app --reload
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-5.6-terra"
uvicorn app:app --reload
```

Then create a new meeting, click **Open discussion**, **Debate round**, select an advisor and type your question, or click **Board summary**. Only **Record decision** closes a meeting.

## What is implemented

- First-person executive boardroom **SVG perspective** (self-contained, no 3D or image dependencies)
- Seven visible members: six specialists and Chief of Staff; clearly defined personalities
- Deterministic meeting-specific advisor selection (three domain advisors + independent Devil's Advocate)
- Separate concurrent OpenAI Responses API HTTP calls per advisor in opening and debate rounds
- Direct address to one specialist, and neutral moderator board summary
- Human-controlled meeting close (decision + optional rationale)
- SQLite storage of agendas, agent opinions, questions, decisions, and a Markdown minutes export
- Demo mode when an API key is not configured; scripted demo is explicitly labeled
- Basic responsive support, server validation, simple error handling

## System map

```text
Browser POV / Meeting UI (web/)
       |
FastAPI endpoints (app.py)
       |      
Meeting Orchestration (select_participants + modes)
       |
Independent model calls (engine.py) ---> OpenAI Responses API
       |
SQLite (meetings / messages / chair's final decision)
```

## API reference

| Endpoint | Use |
|---|---|
| `GET /api/health` | Provider connection status |
| `GET /api/agents` | Advisors and specialties |
| `GET /api/meetings` | Recent board meetings |
| `POST /api/meetings` | Create meeting / route specialists |
| `GET /api/meetings/{id}` | Retrieve a meeting |
| `POST /api/meetings/{id}/opening` | Independent advisor opening round |
| `POST /api/meetings/{id}/debate` | Cross-examination round |
| `POST /api/meetings/{id}/ask` | Chair asks individual specialist |
| `POST /api/meetings/{id}/summary` | Chief of Staff synthesis |
| `POST /api/meetings/{id}/decision` | Chair approves and closes meeting |
| `GET /api/meetings/{id}/export` | Download Markdown minutes |

API docs: http://127.0.0.1:8000/docs

## Production gaps (not yet implemented)

- **Authentication / authorization**: currently assumed single-user local prototype; do not deploy publicly.
- True 3D/photorealistic avatars, motion capture, spatial audio, microphone/voice, lip sync.
- Real-time streaming; current backend collects a whole round before client renders it.
- Live research, file ingestion, source citations, numerical calculation tools, structured evidence scoring.
- Per-member long-term memory, encryption-at-rest, data retention controls, audit trails, rate limits, billing limits, async job queues, WebSockets.
- OpenAI Agents SDK integration: this MVP uses **separate Responses API calls** so orchestration stays transparent, which is fully compatible with later migrating to agents-as-tools / a manager.
- For regulated topics, independent expert verification and human professional advice are still required.

## Privacy note

Data is stored in a plaintext SQLite file locally. The meeting agenda, context, and transcript are sent to the configured model API as part of live agent prompts. Do not use this prototype for confidential company data until authentication, access control, data governance, and storage protection have been added.

## Estimated API usage

Opening = 4 expert calls, one debate round = 3 expert calls, direct question = 1 call, summary = 1 call. Actual usage charges depend on model selection and token counts. The prototype imposes no spending limit; use your API project controls.

## Tests

```bash
pip install httpx pytest
pytest -q
```

## Next milestone

Move room visuals from SVG to WebGL (Three.js / React Three Fiber), add websocket events/turn streaming, optional text-to-speech, evidence tools, user accounts and permission controls. Keep the exact same human-approval boundary.
