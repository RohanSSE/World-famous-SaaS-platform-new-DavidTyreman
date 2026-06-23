# Security Secret Rotation Runbook

Date: 2026-06-23  
Purpose: Close the exposed-secret gap without printing or copying secret values.

## Status

Provider-side rotation is still required. Code cannot truthfully rotate Azure OpenAI, Stripe, or other third-party secrets without dashboard/API access and replacement credentials. Do not claim rotation complete until provider confirmations exist.

## Immediate Rules

- Do not paste secrets into chat, tickets, docs, screenshots, or commits.
- Do not print `GodFather_backend/.env` in terminal output.
- Keep `GodFather_backend/.env` ignored locally.
- Create replacement keys in the provider dashboards before invalidating old keys if the app needs continuity.
- After replacing local/staging/production values, restart services and run smoke tests.

## Rotation Checklist

| Secret Family | Owner | Action | Evidence Required | Status |
|---|---|---|---|---|
| Azure OpenAI endpoint/key/deployment credentials | TBD security/backend owner | Create new key or deployment credential in Azure, update environment stores, revoke old key | Azure rotation timestamp and key ID or masked confirmation | External-blocked |
| Stripe secret key | TBD billing/security owner | Roll secret key in Stripe, update env stores, revoke old key after deploy | Stripe dashboard masked key ID and rotation timestamp | External-blocked |
| Stripe webhook secret | TBD billing/security owner | Generate new webhook signing secret, update deployment env, verify webhook delivery | Successful webhook event after rotation | External-blocked |
| Any other credentials in local `.env` | TBD security owner | Inventory without exposing values, rotate each provider-side secret | Provider-specific confirmation | External-blocked |

## Post-Rotation Verification

| Check | Command / Evidence |
|---|---|
| Backend starts | `python manage.py check` |
| ORB endpoint still responds | Run `GodFather_backend/scripts/recovery-demo-rehearsal.ps1` with valid auth/server |
| AI knowledge build still works | `python manage.py build_ai_knowledge --force --sync` |
| Stripe integration smoke test | Test checkout/webhook in provider sandbox or staging |

## Client-Safe Language

Secrets were exposed in working context and must be rotated in provider dashboards. The repository now has a rotation runbook and local `.env` ignore protection, but actual completion requires the provider owners to rotate and confirm replacement credentials.
