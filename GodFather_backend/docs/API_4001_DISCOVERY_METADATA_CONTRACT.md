# API Contract: discovery_metadata (Backend -> 4001 Service Team)

Date: 2026-06-11
Status: Backend response enrichment (phase 1)

## Scope

This contract describes the new top-level `discovery_metadata` object injected into existing API responses.
No endpoint path changes are required.

## Updated Endpoints

1. `POST /brandgodfather/answer/`
2. `POST /api/sessions/{id}/rag-query/`
3. `POST /api/sessions/admin/rag-dev/test-query/`

`discovery_metadata` is top-level in each response payload when session context exists.

## Design Constraints (as requested)

- Always consume live question list from `http://localhost:4001/phase-questions/`
- Return `discovery_metadata` as a new top-level response object
- Keep existing endpoint contracts backward-compatible
- Vision, Mission, and Customer Profiles may be provisional before Q30 with low confidence
- Brand Type restricted to exact allowed set
- Archetypes flexible but mapped to provided lists
- Confidence scores are float `0.0` to `10.0`
- Confidence bands: `weak`, `generic`, `vendor`, `strong`
- Boundary checkpoint behavior at Q4, Q9, Q19, Q29, Q30
- ORB quote generated and returned at boundary checkpoints

## `discovery_metadata` JSON Shape

```json
{
  "question_number": 1,
  "phase_1_segment": "profiling",
  "boundary_checkpoint": false,
  "live_questions": {
    "source": "live_4001",
    "source_url": "http://localhost:4001/phase-questions/",
    "fetch_ok": true,
    "count": 30
  },
  "brand_type": {
    "name": "Aspirational",
    "confidence": 2.0,
    "band": "generic"
  },
  "vision": {
    "value": "Provisional: vision needs more depth.",
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "mission": {
    "value": "Provisional: mission needs more specificity.",
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "brand_promise": {
    "value": "Provisional: promise is still forming.",
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "brand_story": {
    "value": "Provisional: story arc is still emerging.",
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "customer_profiles": {
    "demographics": {
      "age": "unknown",
      "gender": "unknown",
      "income": "unknown",
      "occupation": "unknown",
      "location": "unknown"
    },
    "psychographics": {
      "values": [],
      "beliefs": [],
      "aspirations": [],
      "frustrations": [],
      "motivations": [],
      "emotional_drivers": []
    },
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "archetypes": {
    "brand": [
      {"name": "Creator", "confidence": 2.6, "band": "generic"},
      {"name": "Explorer", "confidence": 2.2, "band": "generic"},
      {"name": "Sage", "confidence": 1.8, "band": "weak"}
    ],
    "customer": [
      {"name": "Achiever", "confidence": 2.6, "band": "generic"},
      {"name": "Dreamer", "confidence": 2.2, "band": "generic"},
      {"name": "Builder", "confidence": 1.8, "band": "weak"}
    ]
  },
  "three_word_persona": {
    "value": [],
    "examples": [
      "Apple | Imagination. Design. Innovation.",
      "Aston Martin | Power. Beauty. Soul.",
      "Virgin Atlantic | Rebellious. Champion. Maverick.",
      "New Musical Express | Hip. Young. Gunslingers.",
      "Sex Pistols | Rude. Obnoxious. Anarchists."
    ],
    "confidence": 2.0,
    "band": "generic"
  },
  "strategic_opportunities": {
    "items": [],
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "campaign_recommendations": {
    "items": [],
    "confidence": 2.0,
    "band": "generic",
    "provisional": true
  },
  "orb_quote": {
    "enabled": false,
    "quote": "",
    "confidence": 2.0,
    "band": "generic"
  },
  "mandatory": {
    "vision": true,
    "mission": true,
    "customer_profiles": true
  }
}
```

## Confidence Band Mapping

- weak: `0.0 <= score < 2.0`
- generic: `2.0 <= score < 4.0`
- vendor: `4.0 <= score < 6.0`
- strong: `6.0 <= score <= 10.0`

## Frontend Consumption Guidance (4001)

1. Do not remove existing parsing logic for old fields.
2. If `discovery_metadata` exists, prefer it for ORB displays.
3. ORB quote should render when `discovery_metadata.orb_quote.enabled == true`.
4. Use `question_number` + `phase_1_segment` for timeline progress UI.
5. Keep fallback rendering if `live_questions.fetch_ok == false`.

## Backward Compatibility

- Existing response keys remain unchanged.
- `discovery_metadata` is additive only.

## Notes

- `phase_1_segment` uses ranges:
  - Q1-4: profiling
  - Q5-9: revealing_themes
  - Q10-19: identifying_patterns
  - Q20-29: strategic_opportunities
  - Q30: synthesis
