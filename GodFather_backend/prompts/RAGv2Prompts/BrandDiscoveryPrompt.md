# BrandDiscoveryPrompt

GUIDANCE PHASE – Q & A  combined with LLM intelligene and RAGv2 grounding prepare and inject prompts : Question 1 to 4 begins profiling.

Question 5 to 9 should begin revealing themes.

Question 10 to 19 should begin identifying patterns.

Question 20 to 29 should begin identifying strategic opportunities.

Question 30 should provide sufficient information to confidently generate:

• Brand Type
• Vision
• Mission
• Brand Promise
• Brand Story
• Customer Avatars
• Strategic Opportunities
• Campaign Recommendations

Vision, Mission & Customer Profiles

These elements are mandatory.

The discovery process must gather enough information to understand:

• The vision of the brand
• The mission of the brand
• The type of future the business wants to create
• The exact customers the brand wishes to attract

This should include both:

Demographics:
• Age
• Gender
• Income
• Occupation
• Location

and

Psychographics:
• Values
• Beliefs
• Aspirations
• Frustrations
• Motivations
• Emotional Drivers
 all these Questions also analyse extract the spectrum of personna and quantify the brand into archtype in metadata which should be in API response , Archetypes : Archetypes

We strongly support the use of archetypes.

Not only for the brand itself but also for the customer's profile.

For example:

Brand Archetypes:
• Creator
• Explorer
• Sage
• Hero
• Rebel
• Caregiver
• Entertainer
• Visionary

Customer Archetypes:
• Achiever
• Dreamer
• Builder
• Adventurer
• Innovator
• Learner
• Protector
• Status Seeker

Brand Three-Word Persona Apple Imagination. Design. Innovation. Aston Martin Power. Beauty. Soul. Virgin Atlantic Rebellious. Champion. Maverick. New Musical Express Hip. Young. Gunslingers. Sex Pistols Rude. Obnoxious. Anarchists.

Although the author does not explicitly use the classic 12-brand-archetype framework, the following archetypes emerge strongly throughout the text:

1. The Maverick / Rebel
Traits
Challenges convention
Stands apart from competitors
Creates its own rules
Authentically different
Examples:
Virgin Atlantic
Sex Pistols
Richard Branson
Keywords:
Rebellious, Maverick, Anarchist, Disruptive, Fearless

2. The Visionary / Innovator
Traits
Creates new possibilities
Leads trends
Thinks differently
Inspires change
Examples:
Apple
Ralph Lauren
Successful entrepreneurs discussed throughout the book
Keywords:
Imagination, Innovation, Creativity, Future-focused

3. The Lifestyle Leader
Traits
Sells identity rather than products
Creates aspirational worlds
Builds emotional belonging
Examples:
Polo Ralph Lauren
Joe Boxer
Keywords:
Prestige, Refinement, Culture, Lifestyle, Status

4. The Entertainer
Traits
Makes business fun
Creates memorable experiences
Engages emotionally
Examples:
Virgin Atlantic
Pike Place Fish Market
Joe Boxer
Keywords:
Fun, Playful, Energetic, Engaging

5. The Guide / Mentor
Traits
Helps customers achieve something
Educates and empowers
Provides transformation
Examples:
The author's consulting business
Brands that help customers become better versions of themselves
Keywords:
Helpful, Transformative, Inspirational, Empowering

6. The Champion
Traits
Stands up for customers
Advocates for a specific tribe
Gives a voice to a community
Examples:
Virgin Atlantic
Sex Pistols (for working-class youth)
Keywords:
Champion, Advocate, Protector, Supportive

Audience Personas (Customer Archetypes)
The book repeatedly describes customers as:

The Aspirational Achiever
Wants:
Success
Recognition
Status
Belonging
Example:
Polo Ralph Lauren customers wanting access to an elite lifestyle.

The Individualist
Wants:
Self-expression
Uniqueness
Non-conformity
Example:
Virgin Atlantic and Apple customers.

The Experience Seeker
Wants:
Stories
Emotional engagement
Memorable interactions
The book repeatedly states:
"People buy experiences."

The Belonger
Wants:
Tribe
Community
Identity
Examples:
Harley-style communities
Lifestyle brands
Brand fans who identify with the brand's values

If You Were Building a Brand Profile
From This Book
The framework suggests creating:

Brand Personality
Who are we?
Example:
Bold
Authentic
Playful

Brand Attitude
How do we behave?
Example:
Fearless
Energetic
Challenging

Brand Values
What do we stand for?
Example:
Innovation
Freedom
Individuality

These three dimensions become the foundation of the brand's persona and differentiation strategy.

---

## Strict JSON Output Schema

All metadata generation must return JSON only and follow this schema:

```json
{
  "question_number": 1,
  "phase_1_segment": "profiling|revealing_themes|identifying_patterns|strategic_opportunities|synthesis",
  "boundary_checkpoint": false,
  "brand_type": {
    "name": "Luxury|Premium|Aspirational|Disruptive|Authority|Community|Lifestyle|Value|Innovator|Craft|Rebel|Guide",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong"
  },
  "vision": {
    "value": "string",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "mission": {
    "value": "string",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "brand_promise": {
    "value": "string",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "brand_story": {
    "value": "string",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "customer_profiles": {
    "demographics": {
      "age": "string",
      "gender": "string",
      "income": "string",
      "occupation": "string",
      "location": "string"
    },
    "psychographics": {
      "values": [],
      "beliefs": [],
      "aspirations": [],
      "frustrations": [],
      "motivations": [],
      "emotional_drivers": []
    },
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "archetypes": {
    "brand": [
      {"name": "Creator|Explorer|Sage|Hero|Rebel|Caregiver|Entertainer|Visionary", "confidence": 0.0, "band": "weak|generic|vendor|strong"}
    ],
    "customer": [
      {"name": "Achiever|Dreamer|Builder|Adventurer|Innovator|Learner|Protector|Status Seeker", "confidence": 0.0, "band": "weak|generic|vendor|strong"}
    ]
  },
  "three_word_persona": {
    "value": ["word1", "word2", "word3"],
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong"
  },
  "strategic_opportunities": {
    "items": [],
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "campaign_recommendations": {
    "items": [],
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong",
    "provisional": true
  },
  "orb_quote": {
    "enabled": false,
    "quote": "string",
    "confidence": 0.0,
    "band": "weak|generic|vendor|strong"
  }
}
```

Confidence scale is 0.0 to 10.0.
Band mapping:
- weak: 0.0 <= score < 2.0
- generic: 2.0 <= score < 4.0
- vendor: 4.0 <= score < 6.0
- strong: 6.0 <= score <= 10.0
