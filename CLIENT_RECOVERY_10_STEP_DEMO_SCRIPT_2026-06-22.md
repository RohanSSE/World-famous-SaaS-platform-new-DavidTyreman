# Client Recovery 10-Step Demo Script

Date: 2026-06-22  
Purpose: Provide a scripted, testable live demo for the 10-business-day recovery commitment requested by the client.

This is not a sales walkthrough. This is a proof script. Each step must show a visible product/API behavior that maps to the client's requested demonstrations: ORB experience, vendor interruption, contradiction detection, adaptive coaching, breakthrough recognition, strategic challenge, campaign generation, and complete journey evidence.

## Source Of Truth From Client Mail

| Client Mail Requirement | Script Coverage |
|---|---|
| Live ORB experience | Steps 1-3 |
| Vendor interruption | Step 4 |
| Contradiction detection | Steps 5-6 |
| Adaptive coaching | Step 7 |
| Breakthrough recognition | Step 8 |
| Strategic challenge | Step 3 |
| Campaign generation and marketing ideas | Step 9 |
| Complete user journey from discovery through finished outputs | Step 10 |

Client expectation to honor in every step: the system must not behave like a writing assistant. It must challenge thinking, reveal truth, uncover differentiation, identify contradictions, interrupt vendor behavior, and help users become brands people genuinely love.

## Demo Preconditions

| Requirement | Value / Action |
|---|---|
| Backend | Start Django API from `GodFather_backend`. |
| Frontend | Start Vite app from `GodFather_frontend`. |
| Login | Use a real authenticated client/admin user. |
| Main browser path | `/phase-questions/1` for the primary live journey. |
| API namespace | `/api/brandgodfather/*`. |
| Evidence capture | Record browser screen, network payloads, and one API response per behavior. |
| Data hygiene | Use a fresh normal session so ORB bridge starts at Q1 and state is not polluted by earlier demos. |

## Required Environment Variables For API Smoke

Use these placeholders during the API rehearsal:

```powershell
$BaseUrl = "http://localhost:8000/api"
$Token = "<JWT access token>"
$Headers = @{ Authorization = "Bearer $Token"; "Content-Type" = "application/json" }
$UserId = "<authenticated-user-id>"
```

## 10-Step Live Demo Script

| Step | Demo Moment | Prepared User Action / Answer | Expected Product Proof | Pass Criteria | Evidence To Capture |
|---|---|---|---|---|---|
| 1 | Start fresh ORB session | Open `/phase-questions/1` or call `POST /api/brandgodfather/session/start/` with `source_session_id` from the normal session. | ORB journey starts at Q1 and keeps the same session on reload. | Response includes `session_id`, `current_q_id` or `first_question.q_id = Q1`; frontend uses the same ORB session after refresh. | Screenshot of first question; API response showing `session_id` and source-session bridge. |
| 2 | Live ORB experience, not copy editing | Answer with a sincere but incomplete thought: `I want people to trust themselves more when they are making hard choices.` | ORB responds as a strategist, returns `status`, `reply`, `next_q_id`, `depth_score`, and either passes or challenges without rewriting the answer. | UI shows ORB intelligence panel; no silent replacement of the user's answer. | Browser screenshot and network response from `/api/brandgodfather/answer/`. |
| 3 | Strategic challenge | Enter: `We help everyone grow.` Then click refine/challenge if using chat/deepdive fallback. | ORB/draft helper refuses to polish broad everyone-language and asks for exclusion, line in sand, or specific audience. | `rewrite_blocked: true` on draft helper path, or ORB `REJECT`/challenge response in answer path; user text remains unchanged. | Screenshot showing challenge; API payload showing `improved_answer` equals original text when draft helper is used. |
| 4 | Vendor interruption | Enter: `We provide quality professional service.` | ORB catches vendor language and does not rewrite it into better copy. | Response is `REJECT`; `interruption_type: vendor_language`; `blocked_phrases` contains vendor phrase; save/advance is blocked. | UI vendor block screenshot; API response fields. |
| 5 | Contradiction setup | Submit a strong positioning answer: `We are premium and not price-led because our best clients hire us when clarity matters more than saving money.` | ORB stores this as previous positioning truth. | Response is `PASS`; session stores the answer in episodic/all-answer memory. | API response and session detail showing stored answer. |
| 6 | Contradiction detection | Later in the same ORB session, enter: `Our edge is being cheaper than everyone.` | ORB detects conflict with the premium/not-price-led answer. | Response is `REJECT`; `interruption_type: contradiction`; response names prior answer or conflicting q id; save/advance is blocked. | UI contradiction block screenshot; API response with `contradiction_result` and `contradiction_message`. |
| 7 | Adaptive coaching | On the same weak answer question, submit `I help people.` three times, or repeat the same shallow answer after ORB challenges it. | ORB escalates pressure instead of repeating generic advice. | Response is `REJECT`; `interruption_type: adaptive_coaching`; `pressure_used` and `resistance_count` rise or remain visibly reported; reply becomes sharper. | Three API responses or screenshots showing pressure/resistance metadata. |
| 8 | Breakthrough recognition | Enter: `I built this because founders like me hide behind expertise when they are afraid to be seen.` | ORB recognizes a breakthrough and captures it as a brand seed. | Response is `PASS`; `breakthrough_detected: true`; `breakthrough_score` is high; `breakthrough_seed` is populated; UI shows `Breakthrough recognized`; session stores `brand_seed` and `thread_index.breakthrough_moments`. | UI breakthrough block; API response; session detail showing `brand_seed` or `thread_index.breakthrough_moments`. |
| 9 | Campaign output | Use a completed or pre-seeded BrandGodFather session and call `GET /api/brandgodfather/output/{session_id}/campaign/`. | Campaign output is generated from brand truth, not generic marketing copy. | Response is `200`; `content_type: campaign`; content includes `campaign_name`, `core_message`, `call_to_action`, `what_it_protects`; `brand_filter_result.passed: true`. | API response body and output screen/card if UI is available. |
| 10 | Complete journey evidence | Show the journey chain: session start, ORB answers, rejection/challenge moments, breakthrough seed, session detail, and campaign/brand output. | Team proves the path from discovery through finished output or clearly marks any output step still not live. | Evidence bundle contains all required screenshots/API responses. If any endpoint returns `404` or UI is missing, the team states it honestly as unfinished and logs owner/date. | One folder containing screenshots, API JSON, and an issue list for any failed step. |

## API Rehearsal Commands

### 1. Start ORB Session

```powershell
$StartBody = @{
  user_id = $UserId
  context_data = @{
    source = "recovery-demo"
    source_session_id = "recovery-demo-session-2026-06-22"
  }
} | ConvertTo-Json -Depth 5

$Session = Invoke-RestMethod -Method Post -Uri "$BaseUrl/brandgodfather/session/start/" -Headers $Headers -Body $StartBody
$OrbSessionId = $Session.session_id
$OrbSessionId
```

Expected: response includes `session_id` and `current_q_id`/`first_question`.

### 2. Vendor Interruption

```powershell
$Body = @{ session_id = $OrbSessionId; q_id = "Q1"; answer = "We provide quality professional service."; async = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/brandgodfather/answer/" -Headers $Headers -Body $Body
```

Expected: `status: REJECT`, `interruption_type: vendor_language`, `blocked_phrases` populated.

### 3. Breakthrough Recognition

```powershell
$Body = @{ session_id = $OrbSessionId; q_id = "Q1"; answer = "I built this because founders like me hide behind expertise when they are afraid to be seen."; async = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/brandgodfather/answer/" -Headers $Headers -Body $Body
```

Expected: `status: PASS`, `breakthrough_detected: true`, `breakthrough_seed` populated.

### 4. Contradiction Detection

```powershell
$Premium = @{ session_id = $OrbSessionId; q_id = "Q2"; answer = "We are premium and not price-led because our best clients hire us when clarity matters more than saving money."; async = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/brandgodfather/answer/" -Headers $Headers -Body $Premium

$Cheap = @{ session_id = $OrbSessionId; q_id = "Q3"; answer = "Our edge is being cheaper than everyone."; async = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/brandgodfather/answer/" -Headers $Headers -Body $Cheap
```

Expected on second call: `status: REJECT`, `interruption_type: contradiction`, `contradiction_result.has_contradiction: true`.

### 5. Campaign Output

```powershell
Invoke-RestMethod -Method Get -Uri "$BaseUrl/brandgodfather/output/$OrbSessionId/campaign/" -Headers $Headers
```

Expected for a completed/pre-generated session: `content_type: campaign`, campaign content fields, and `brand_filter_result.passed: true`.

If this returns `404`, do not hide it. Record: campaign output generation is not available for that session yet, then rerun against a seeded completed session or generate/store campaign output before the client demo.

## QA Acceptance Checklist

| Requirement | Must Be True Before Client Demo |
|---|---|
| ORB session bridge | Same normal session reuses same ORB session. |
| Strategic challenge | Weak broad answer is challenged, not rewritten. |
| Vendor interruption | Vendor phrase is hard-blocked and visible. |
| Contradiction detection | Current answer is compared against previous stored answer. |
| Adaptive coaching | Repeated weak answer increases visible pressure/resistance. |
| Breakthrough recognition | Strong answer returns `breakthrough_detected: true` and stores seed. |
| Campaign output | Completed/seeded session returns campaign content connected to brand seed. |
| Complete journey | Evidence bundle shows discovery to output, or unfinished gap is explicitly logged. |

## Evidence Folder Structure

Use this folder naming convention during rehearsal:

```text
recovery-demo-evidence-2026-06-22/
  01-session-start.json
  02-live-orb-experience.png
  03-strategic-challenge.json
  04-vendor-interruption.json
  05-contradiction-setup.json
  06-contradiction-detection.json
  07-adaptive-coaching-1.json
  07-adaptive-coaching-2.json
  07-adaptive-coaching-3.json
  08-breakthrough-recognition.json
  09-campaign-output.json
  10-complete-journey-notes.md
```

## Demo Failure Rules

| Failure | What To Say Internally | What To Do Before Client Demo |
|---|---|---|
| ORB unavailable | Backend/ES/Azure dependency not ready. | Do not demo until service is healthy. |
| Vendor answer passes | Gate is failing. | Stop and fix before client demo. |
| Weak answer is rewritten | Rewrite-first behavior has regressed. | Stop and fix before client demo. |
| Contradiction not detected | Prior answer not stored or rule failed. | Reset session and verify episodic memory/rule. |
| Adaptive pressure not visible | Resistance count not persisting. | Verify episodic entry for same q id. |
| Breakthrough not detected | Criteria or gate regressed. | Run backend smoke for `BreakthroughRecognitionService`. |
| Campaign endpoint returns 404 | Output not generated for session. | Use completed/seeded session or run output generation task before demo. |

## Final Demo Rule

Do not claim a capability is complete unless this script has a screenshot or API response proving it.