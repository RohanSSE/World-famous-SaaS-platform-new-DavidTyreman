# Live Demo Evidence Runbook

Date: 2026-06-23  
Purpose: Capture the proof David asked for: live ORB behavior, API evidence, campaign output, and complete journey evidence.

## Status

The automated API rehearsal script exists at `GodFather_backend/scripts/recovery-demo-rehearsal.ps1`. It has not been executed in this session because a running backend URL, a valid user token, and a real user id were not available. Do not claim live evidence captured until the script writes an evidence folder with JSON responses and screenshots/network proof.

## Required Inputs

| Input | Example | Source |
|---|---|---|
| Backend base URL | `http://127.0.0.1:8000/api` | Running backend |
| Bearer token | Do not paste in chat | Authenticated local/staging user |
| User id | Numeric user id | Authenticated user/session |
| Evidence output folder | `GodFather_backend/evidence/recovery-demo-YYYYMMDD-HHMMSS` | Script default |

## API Evidence Command

Run from the repository root after backend is running and auth is ready:

```powershell
Set-Location GodFather_backend
./scripts/recovery-demo-rehearsal.ps1 -BaseUrl "http://127.0.0.1:8000/api" -Token "<type-token-directly-in-terminal>" -UserId <user-id>
```

## Evidence Expected

| Evidence File | Proves |
|---|---|
| `01-session-start.json` | ORB session bridge starts/reuses a session |
| `02-live-orb-answer.json` | ORB responds as strategist, not copy editor |
| `03-strategic-challenge.json` | Broad answer is challenged and not silently rewritten |
| `04-vendor-interruption.json` | Vendor language is rejected/interrupted |
| `05-contradiction-setup.json` | Prior positioning truth is stored |
| `06-contradiction-detected.json` | Contradiction blocks progression |
| `07-adaptive-coaching-*.json` | Resistance/pressure escalation is visible |
| `08-breakthrough-recognition.json` | Breakthrough flag, score, and seed are returned |
| `09-session-detail.json` | Memory includes seed/thread evidence |
| `10-campaign-output.json` | Campaign output path returns generated/stored output |
| `11-complete-journey-notes.md` | Human notes on pass/fail for full journey |

## Client-Safe Language

The demo script and acceptance path are ready. Live proof still requires a real run with valid auth and server, plus screenshots/network capture for the browser UI.
