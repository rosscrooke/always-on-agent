"""
The agent's structured output — the "form" it fills instead of writing prose.

This is workshop Lever 3 (structured output): downstream systems (the dashboard,
Slack, a ticket) consume these fields directly, and it keeps the agent cheap and
auditable. The `evidence` field is the audit trail (which change / metric proves
the cause).
"""

# Actions the agent is allowed to recommend. 'none' = no change warranted.
ACTION_TYPES = [
    "lower_floor",         # fill drop caused by a raised eCPM floor
    "restore_targeting",   # fill drop caused by narrowed targeting
    "restore_priority",    # underpacing caused by a competing line item raised in priority
    "raise_priority",      # underpacing / unspent budget — capture more inventory
    "fix_creative",        # creative disapproved — fix the policy violation
    "fallback_creative",   # swap back to the last approved creative to protect the slot
    "none",                # nothing to do
]

SEVERITIES = ["low", "medium", "high", "critical"]

# JSON Schema used as the input_schema of the submit_recommendation tool, so the
# model is forced to return exactly these fields.
RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "campaign_id": {"type": "string", "description": "The issue ID, e.g. CAMP-1001"},
        "issue_summary": {"type": "string", "description": "One sentence: what is wrong"},
        "likely_cause": {"type": "string", "description": "The single most likely root cause"},
        "evidence": {
            "type": "string",
            "description": "Cite the specific change ID(s), timestamps, or metrics that support the cause. Never invent change IDs — if no related change exists, say so.",
        },
        "recommended_action": {"type": "string", "description": "The concrete next step to protect revenue"},
        "action_type": {"type": "string", "enum": ACTION_TYPES},
        "severity": {"type": "string", "enum": SEVERITIES},
        "requires_human_approval": {
            "type": "boolean",
            "description": "MUST be true for any action that changes ad serving (floors, priority, targeting, creatives).",
        },
        "expected_impact": {
            "type": "string",
            "description": "Quantified expected effect, e.g. '+13,600 impressions/hour recovered' or 'protects 2M-impression guarantee'.",
        },
    },
    "required": [
        "campaign_id", "issue_summary", "likely_cause", "evidence",
        "recommended_action", "action_type", "severity",
        "requires_human_approval", "expected_impact",
    ],
}
