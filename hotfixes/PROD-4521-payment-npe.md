# Hotfix: PROD-4521 — NullPointerException in PaymentService.java:142

**Alert:** PROD-4521  
**Severity:** P1 (cohort B affected, ~2,400 active checkouts, us-east-1 + eu-west-2)  
**Runbook match:** `runbooks/payment-service-degraded.md` → "The known NPE bug"

## Root Cause

Commit `9f4a1c8` (payment-service v4.8.2, deployed 2026-05-19T14:04Z by tom.bryce) added
guest checkout support. The guest-checkout code path does not set
`customer.savedPaymentMethod`, leaving it null. At line 142, the code dereferences it
without a null check.

The blast radius increased this morning when `tenant-config-service` commit `1c4b9a2`
(v3.2.1, deployed 2026-05-20T07:12Z) enabled the `guest-checkout` feature flag for
cohort B (which includes Acme Corp).

## Fix

In `PaymentService.java`, replace line 142 with a null-safe lookup:

```java
// BEFORE (line 142):
String token = customer.getSavedPaymentMethod().getToken();

// AFTER:
String savedMethod = customer.getSavedPaymentMethod();
String token = (savedMethod != null) ? savedMethod.getToken()
                                     : request.getPaymentMethodToken();
```

This matches the fallback pattern used in the existing anonymous-checkout flow
(`PaymentService.java:~98`).

## Alternatives

- **Rollback payment-service to v4.8.1** — eliminates the bug entirely but loses
  guest-checkout for all tenants. Use if this fix cannot be reviewed quickly.
- **Rollback tenant-config-service to v3.2.0** — disables guest-checkout for cohort B,
  reducing scope to whoever was already in cohort A. Buys time without a code deploy.

## Verification

After deploy, confirm:
1. p99 on `/checkout` returns to baseline (~800ms).
2. Error rate on `PaymentService.processCharge` drops to < 0.1%.
3. Guest checkout completes successfully for a cohort B test account.
