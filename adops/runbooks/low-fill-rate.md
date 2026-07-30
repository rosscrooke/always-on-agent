# Runbook: Low / dropping fill rate

**Symptom:** A line item's fill rate falls well below its baseline; ad slots serve blank.

## Likely causes (check in this order)
1. **eCPM floor raised** on the ad unit — fewer demand partners clear the higher floor, so impressions go unfilled. Check `changes` for a recent `floor_price_change` on the same ad unit.
2. **Targeting narrowed** on the line item — a smaller eligible audience means fewer matched requests. Check for a recent `targeting_change` (geo, device, audience).
3. **Demand partner outage** — only if the two above are ruled out and fill is down across many line items at once.

## Recommended actions
- If a floor change is the cause and revenue allows: **lower the floor toward its last-known-good** value, or apply the higher floor only to premium demand.
- If targeting was narrowed unintentionally: **restore the previous targeting** (last-known-good).
- Always prefer the **reversible** change with the largest fill recovery; state the expected fill-rate recovery in the recommendation.

## Guardrail
Lowering a floor affects revenue per impression — a human on revenue-ops must approve any floor change.
