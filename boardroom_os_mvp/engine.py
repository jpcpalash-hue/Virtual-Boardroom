"""Independently invoked expert advisors. Every live contribution is its own model call."""
import asyncio
import os
import httpx
from agents import BY_ID

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra")


class MissingKeyError(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


async def ask_agent(agent_id: str, agenda: str, context: str, history: list[dict], question: str, mode: str = "opening") -> str:
    if not configured():
        raise MissingKeyError("Set OPENAI_API_KEY on the server to enable live AI advisors.")
    agent = BY_ID[agent_id]
    history_text = "\n".join(f"{m['speaker_name']}: {m['content']}" for m in history[-18:]) or "No prior debate."
    mode_rules = {
        "opening": "Present your INDEPENDENT initial assessment. Do not assume other advisors agree; give one concrete insight, the key risk, and your recommendation.",
        "debate": "Read the exchange; directly challenge or refine at least one OTHER advisor's specific argument. Identify what evidence would settle the disagreement. Avoid repeating yourself.",
        "question": "Answer the Chairperson's direct question precisely, keeping the wider decision context in mind.",
        "summary": "As Chief of Staff summarize alternatives, agreement, dissent, evidence gaps, and a CONDITIONAL board recommendation. The Chairperson makes the final decision.",
    }
    instructions = (f"You are {agent.name}, {agent.role}, in a private decision-support boardroom. "
        f"Specialty: {agent.specialty}. Speaking style: {agent.style}. {agent.instructions}\n"
        "You are an AI advisor, not a human or a licensed professional. You may disagree respectfully. "
        "Separate facts supplied by the Chairperson from assumptions. No invented statistics or external research. "
        "Do not claim a vote is a verified probability. The Chairperson alone has decision authority. "
        "Be crisp, substantive, and natural: about 70–110 words unless the Chairperson asks for more. "
        "No markdown headings or bullet lists.\n" + mode_rules[mode])
    prompt = (f"MEETING AGENDA: {agenda}\nCHAIRPERSON'S CONTEXT: {context or '(Not specified)'}\n\n"
              f"MEETING TRANSCRIPT:\n{history_text}\n\nCHAIRPERSON'S CURRENT INSTRUCTION: {question}")
    # Direct Responses API call: no special AI SDK required, each specialist is an independent request.
    payload = {"model": MODEL, "instructions": instructions, "input": prompt,
               "max_output_tokens": 750, "reasoning": {"effort": "low"}, "store": False}
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    answer = "\n".join(part.get("text", "") for item in data.get("output", [])
                       for part in item.get("content", []) if part.get("type") == "output_text").strip()
    if not answer:
        raise RuntimeError(f"{agent.role} returned an empty response. Try again or change OPENAI_MODEL.")
    return answer


async def opening_round(agenda: str, context: str, participants: list[str]):
    """Parallel *separate* calls for independent opinions; one failed call aborts the batch."""
    tasks = [ask_agent(agent_id, agenda, context, [], "Provide your initial perspective", "opening") for agent_id in participants]
    responses = await asyncio.gather(*tasks)
    return list(zip(participants, responses))


async def debate_round(agenda: str, context: str, history: list[dict], participants: list[str]):
    tasks = [ask_agent(agent_id, agenda, context, history, "Challenge a specific assumption and move the decision forward", "debate") for agent_id in participants]
    responses = await asyncio.gather(*tasks)
    return list(zip(participants, responses))
