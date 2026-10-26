"""Board member definitions. Keep expertise separate from orchestration."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BoardAgent:
    id: str
    name: str
    role: str
    specialty: str
    style: str
    instructions: str
    color: str


AGENTS = [
    BoardAgent("chief", "Alex Morgan", "Chief of Staff", "Meeting facilitation", "Measured · neutral", "Facilitate fairly; distinguish what was decided from what remains open. Never decide for the Chairperson.", "#c4a675"),
    BoardAgent("strategy", "Victoria Chen", "Strategy Director", "Corporate strategy", "Long-term · incisive", "Focus on competitive advantage, option value, second-order effects, and long-term positioning. Make explicit strategic tradeoffs.", "#7db7de"),
    BoardAgent("finance", "Daniel Reed", "Finance Director", "Finance and investment", "Quantitative · disciplined", "Focus on cash flow, opportunity cost, ROI/NPV, sensitivity analysis. Never invent financial figures; specify inputs required.", "#80c8a9"),
    BoardAgent("risk", "Amara Okafor", "Chief Risk Officer", "Risk and uncertainty", "Skeptical · rigorous", "Consider downside scenarios, probability/impact ranges, reversibility, weak assumptions and mitigations. Avoid invented probabilities.", "#e0ab86"),
    BoardAgent("operations", "Elena Brooks", "Operations Director", "Execution and operations", "Pragmatic · operational", "Focus on practical delivery, dependencies, capability and resource constraints, bottlenecks, milestones, and measurable KPIs.", "#ae9ce4"),
    BoardAgent("technology", "Noah Patel", "Technology Director", "Technology and data", "Technical · systems-minded", "Test architecture, scalability, security, data quality, build-vs-buy, maintainability and implementation complexity.", "#89c7cf"),
    BoardAgent("devil", "Marcus Vale", "Devil's Advocate", "Independent challenge", "Contrarian · precise", "Challenge the strongest assumptions and comfortable consensus; steelman opposing explanations, but do not be contrarian without substantive grounds.", "#ef929b"),
]

BY_ID = {agent.id: agent for agent in AGENTS}
VISIBLE_MEMBERS = ["strategy", "finance", "operations", "risk", "technology", "devil", "chief"]

TOPIC_KEYWORDS = {
    "finance": ("salary", "pay", "money", "cost", "investment", "budget", "loan", "roi", "cash", "revenue", "profit", "pricing", "offer"),
    "technology": ("software", "app", "ai", "data", "tech", "platform", "build", "api", "digital", "cloud", "model", "cyber"),
    "operations": ("supply", "operation", "process", "manufactur", "implement", "launch", "delivery", "capacity", "vendor", "project"),
    "risk": ("risk", "uncertain", "regulat", "compliance", "career", "job", "offer", "market", "invest", "decide"),
    "strategy": ("strateg", "career", "growth", "business", "expansion", "competi", "choice", "choose", "startup", "offer"),
}


def select_participants(agenda: str, limit: int = 4) -> list[str]:
    """Deterministic, transparent routing for the MVP. No hidden AI router."""
    topic = agenda.lower()
    scores = {agent_id: sum(token in topic for token in words) for agent_id, words in TOPIC_KEYWORDS.items()}
    ordered = sorted(scores, key=lambda k: (-scores[k], ["strategy", "finance", "risk", "technology", "operations"].index(k)))
    selected = [agent_id for agent_id in ordered if scores[agent_id] > 0][: max(1, limit - 1)]
    if not selected:
        selected = ["strategy", "finance", "risk"]
    for default in ("strategy", "finance", "risk"):
        if len(selected) >= limit - 1:
            break
        if default not in selected:
            selected.append(default)
    return selected[:limit-1] + ["devil"]


def public_agents():
    return [dict(id=a.id, name=a.name, role=a.role, specialty=a.specialty, style=a.style, color=a.color) for a in AGENTS]
