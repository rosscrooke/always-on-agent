"""
THE AGENT BRAIN — triage one ad-ops campaign issue into a structured recommendation.

Flow (an agentic loop):
  1. Read the campaign issue.
  2. The model decides which tools to call — pull the recent-changes log, the
     relevant runbook, the ad policy — to find the root cause.
  3. It calls submit_recommendation once with the structured result.
  4. A self-healing GATE checks that result before we accept it; if it fails,
     the model is asked to fix and resubmit.

Only the DATA comes from the adapter, so this brain is identical in demo and
production. Routing + caching (the cost levers) plug in on top of this later —
we get it correct first, then make it cheap, exactly like the workshop.
"""
from __future__ import annotations

import json
import sys

try:  # works both as `python -m src.agent` and `python src/agent.py`
    from .adapters import StubAdapter
    from .config import ADOPS_ROOT, MODEL_STRONG, get_client
    from .schemas import ACTION_TYPES, RECOMMENDATION_SCHEMA
except ImportError:  # pragma: no cover
    from adapters import StubAdapter
    from config import ADOPS_ROOT, MODEL_STRONG, get_client
    from schemas import ACTION_TYPES, RECOMMENDATION_SCHEMA


SYSTEM_PROMPT = """You are an always-on ad-operations copilot for an in-flight entertainment (IFE) ad network.
You watch advertising campaigns running through the ad servers (Google Ad Manager and SpringServe) and,
when a campaign has a problem, you diagnose the cause and recommend the action that protects revenue.

YOUR PROCESS for each campaign issue:
1. Read the issue and its metrics.
2. Call get_recent_changes and look for a change whose timestamp lines up with when the problem started,
   on the same line item or ad unit. That is usually the root cause. NEVER invent a change ID.
3. Call list_runbooks, then get_runbook on the one that matches the symptom, and follow its guidance.
4. For a disapproved/rejected creative, also call get_ad_policy and identify the exact clause violated.
5. Call submit_recommendation exactly once with your structured conclusion.

RULES:
- Cite concrete evidence: the change ID, the timestamp, or the metric. If no related change exists
  (e.g. a pure pacing/budget problem), say so plainly in the evidence.
- Any action that changes how ads serve (floors, priority, targeting, creatives) MUST set
  requires_human_approval = true. You recommend; a human approves. Never act autonomously on revenue.
- If nothing should change, use action_type "none".
- Quantify expected_impact wherever the metrics allow."""


# --- Tool definitions the model can call -------------------------------------

TOOLS = [
    {
        "name": "get_recent_changes",
        "description": "Return the recent ad-ops change log (targeting, floor, priority, creative changes) to correlate against the issue.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_runbooks",
        "description": "List the available ad-ops runbook names.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_runbook",
        "description": "Return the full text of a runbook by name (from list_runbooks).",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Runbook name, e.g. low-fill-rate"}},
            "required": ["name"],
        },
    },
    {
        "name": "get_ad_policy",
        "description": "Return the creative ad policy, for diagnosing a disapproved creative.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "submit_recommendation",
        "description": "Submit your final structured recommendation. Call this exactly once when you are done.",
        "input_schema": RECOMMENDATION_SCHEMA,
    },
]


def _dispatch_tool(name: str, tool_input: dict, adapter) -> str:
    """Run a data tool against the adapter and return a string result."""
    if name == "get_recent_changes":
        return json.dumps(adapter.get_recent_changes(), indent=2)
    if name == "list_runbooks":
        return json.dumps(adapter.list_runbooks())
    if name == "get_runbook":
        return adapter.get_runbook(tool_input["name"])
    if name == "get_ad_policy":
        return adapter.get_ad_policy()
    return f"ERROR: unknown tool {name}"


def _gate(rec: dict) -> list[str]:
    """The self-healing quality gate. Returns a list of problems (empty = passes).

    This is the workshop's 'check before it acts' step: nothing reaches the
    dashboard/Slack until it passes. v1 is programmatic and cheap; it can be
    upgraded to an LLM judge later.
    """
    problems = []
    for field in RECOMMENDATION_SCHEMA["required"]:
        if not str(rec.get(field, "")).strip() and rec.get(field) is not False:
            problems.append(f"missing/empty field: {field}")
    if rec.get("action_type") not in ACTION_TYPES:
        problems.append(f"action_type must be one of {ACTION_TYPES}")
    # Safety rule: any real action must be flagged for human approval.
    if rec.get("action_type") not in (None, "none") and rec.get("requires_human_approval") is not True:
        problems.append("actions that change ad serving must set requires_human_approval = true")
    return problems


def triage_campaign(campaign_id: str, adapter, client=None, model: str = MODEL_STRONG,
                    max_turns: int = 8) -> dict:
    """Run the agentic loop for one campaign and return the accepted recommendation."""
    client = client or get_client()
    campaign = adapter.get_campaign(campaign_id)

    messages = [{
        "role": "user",
        "content": "Triage this campaign issue and submit a recommendation:\n\n"
                   + json.dumps(campaign, indent=2),
    }]

    for _ in range(max_turns):
        resp = client.messages.create(
            model=model, max_tokens=1500, system=SYSTEM_PROMPT,
            tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses:
            # Model answered in prose instead of calling a tool — nudge it back on rails.
            messages.append({"role": "user", "content": "Please call submit_recommendation with your structured conclusion."})
            continue

        tool_results = []
        for tu in tool_uses:
            if tu.name == "submit_recommendation":
                rec = dict(tu.input)
                problems = _gate(rec)
                if not problems:
                    return rec  # accepted
                # Rejected by the gate → tell the model what to fix and let it resubmit.
                tool_results.append({
                    "type": "tool_result", "tool_use_id": tu.id, "is_error": True,
                    "content": "Quality gate REJECTED this. Fix and resubmit: " + "; ".join(problems),
                })
            else:
                tool_results.append({
                    "type": "tool_result", "tool_use_id": tu.id,
                    "content": _dispatch_tool(tu.name, tu.input, adapter),
                })
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"Agent did not produce an accepted recommendation for {campaign_id} within {max_turns} turns")


if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "CAMP-1001"
    adapter = StubAdapter(ADOPS_ROOT)
    result = triage_campaign(cid, adapter)
    print(json.dumps(result, indent=2))
