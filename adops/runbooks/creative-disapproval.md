# Runbook: Creative disapproved / rejected

**Symptom:** A creative is disapproved by the ad server; the line item serves nothing.

## Likely causes (check in this order)
1. **Policy violation** — the creative breaks a rule in `ad-policy.md` (e.g. alcohol without responsibility messaging, missing age-gating, restricted category). Check the creative's category and metadata against policy.
2. **Recently uploaded creative** — check `changes` for a recent `creative_upload`; a new creative replaced an approved one.
3. **Technical issue** — wrong dimensions, file size, or broken click-through (only if policy is clean).

## Recommended actions
- **Identify the exact policy clause** violated and state the fix (add responsibility messaging, add age-gating, restrict placement away from family/kids content).
- If the fix is slow, **fall back to the last approved creative** (last-known-good) to protect the slot from serving blank.
- Never auto-approve a creative — route the fix to trafficking.

## Guardrail
Serving alcohol or restricted-category creatives incorrectly is a compliance risk — a human must approve any creative change.
