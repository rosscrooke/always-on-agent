# Runbook: Campaign underpacing / delivery risk

**Symptom:** A guaranteed line item is projected to deliver below 100% before its end date.

## Likely causes (check in this order)
1. **A competing line item outranks it** — a recent `priority_change` raised another line item in the same ad unit, starving delivery. Check `changes`.
2. **Targeting too narrow** for the remaining goal — not enough eligible impressions.
3. **Goal set too high** for available inventory in the flight window.

## Recommended actions
- If a competing line item was raised in priority and is lower business value: **restore its priority to last-known-good**, or raise the at-risk guaranteed line item's priority to match.
- Estimate the **make-good / under-delivery exposure** (impressions short × contracted CPM) so the business can weigh it.
- Prefer the change that protects the **guaranteed** commitment with the least disruption to other revenue.

## Guardrail
Reprioritizing line items affects other advertisers' delivery — a human must approve any priority change.
