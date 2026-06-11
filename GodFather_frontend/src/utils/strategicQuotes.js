import { JOURNEY_PHASES, getPhaseAnswersStorageKey } from "../constants/journeyPhases";

const QUOTE_BANK = [
  {
    id: "know-thyself",
    text: "Know Thyself.",
    author: "Inscribed on the Oracle Shrine of Apollo",
    themes: ["identity", "self", "truth", "purpose", "origin"],
    contexts: ["phase_intro", "brand_book_loading"],
  },
  {
    id: "meaning",
    text: "Most businesses compete for attention. Strong brands create meaning.",
    author: "The Brand Godfather",
    themes: ["meaning", "attention", "purpose", "customer", "emotion"],
    contexts: ["phase_intro", "phase_complete", "brand_book_page"],
  },
  {
    id: "camouflage",
    text: "Professionalism has become camouflage.",
    author: "The Brand Godfather",
    themes: ["authentic", "professional", "mask", "voice", "truth", "culture"],
    contexts: ["phase_intro", "brand_book_page"],
  },
  {
    id: "only-one",
    text: "Success is not about being perceived as the best at what you do, it is about being perceived as the only one who does what you do.",
    author: "Jerry Garcia, The Grateful Dead",
    themes: ["different", "unique", "only", "category", "positioning", "competition"],
    contexts: ["phase_complete", "brand_book_page"],
  },
  {
    id: "idea",
    text: "America is not just a country, it is an idea.",
    author: "Bono, U2",
    themes: ["idea", "worldview", "belief", "culture", "community", "movement"],
    contexts: ["phase_complete", "brand_book_page"],
  },
  {
    id: "experience",
    text: "The brand is the experience. The product is the souvenir.",
    author: "Nick Graham, Founder, Joe Boxer",
    themes: ["experience", "product", "customer", "service", "touchpoint", "output"],
    contexts: ["brand_book_loading", "brand_book_ready", "output_mode", "brand_book_page"],
  },
  {
    id: "dare",
    text: "Who dares, wins.",
    author: "David Stirling",
    themes: ["courage", "bold", "risk", "brave", "future", "growth"],
    contexts: ["phase_complete", "brand_book_ready", "output_mode"],
  },
];

const CONTEXT_THEME_HINTS = {
  phase_intro: ["identity", "self", "truth", "purpose"],
  phase_complete: ["different", "meaning", "courage", "worldview"],
  brand_book_loading: ["experience", "meaning", "identity", "worldview"],
  brand_book_page: ["identity", "different", "experience", "worldview"],
  brand_book_ready: ["experience", "output", "growth", "courage"],
  output_mode: ["experience", "growth", "customer", "output"],
};

function normalizeText(value) {
  return String(value || "").toLowerCase();
}

function sessionHash(value = "") {
  return String(value).split("").reduce((acc, ch) => (acc + ch.charCodeAt(0)) % 997, 0);
}

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function collectJourneyAnswerText(sessionId) {
  const answers = [];
  for (const phase of JOURNEY_PHASES) {
    const stored = readJson(getPhaseAnswersStorageKey(sessionId, phase.id), {});
    if (!stored || typeof stored !== "object") continue;
    Object.values(stored).forEach((value) => {
      const text = String(value || "").trim();
      if (text) answers.push(text);
    });
  }
  return answers.join("\n");
}

function collectLocalSignal(extraText = "") {
  let sessionId = localStorage.getItem("sessionId") || "";
  let sessionTitle = "";
  try {
    const session = JSON.parse(localStorage.getItem("session") || "{}");
    sessionId = sessionId || String(session?.id ?? session?.pk ?? "");
    sessionTitle = session?.title || "";
  } catch {
    /* ignore */
  }
  const answerText = collectJourneyAnswerText(sessionId || null);
  return {
    sessionId,
    text: [sessionTitle, answerText, extraText].filter(Boolean).join("\n"),
  };
}

function scoreQuote(quote, { context, phaseId, sourceText }) {
  const haystack = normalizeText(sourceText);
  const contextThemes = CONTEXT_THEME_HINTS[context] || [];
  let score = 0;

  if (!quote.contexts.includes(context)) score -= 4;
  quote.themes.forEach((theme) => {
    if (haystack.includes(theme)) score += 4;
    if (contextThemes.includes(theme)) score += 2;
  });

  if (Number(phaseId) === 1 && quote.id === "know-thyself") score += 5;
  if (Number(phaseId) === 2 && quote.id === "only-one") score += 4;
  if (Number(phaseId) === 3 && quote.id === "experience") score += 4;
  if (context === "brand_book_ready" && quote.id === "experience") score += 6;
  if (context === "output_mode" && quote.id === "experience") score += 6;

  return score;
}

function getEvidenceThemes(sourceText, themes) {
  const haystack = normalizeText(sourceText);
  return themes.filter((theme) => haystack.includes(theme)).slice(0, 3);
}

function extractUserQuote(sourceText, context) {
  if (!sourceText || !["brand_book_page", "brand_book_loading"].includes(context)) return null;
  const strongTerms = [
    "believe", "truth", "different", "meaning", "customer", "community", "culture",
    "experience", "purpose", "promise", "future", "identity", "voice", "bold", "trust",
  ];
  const candidates = String(sourceText)
    .split(/(?<=[.!?])\s+|\n+/)
    .map((item) => item.trim().replace(/^[-*]\s*/, ""))
    .filter((item) => {
      const words = item.split(/\s+/).filter(Boolean);
      const lower = item.toLowerCase();
      return words.length >= 7 && words.length <= 26 && strongTerms.some((term) => lower.includes(term));
    });

  if (!candidates.length) return null;
  const picked = candidates.sort((a, b) => {
    const aScore = strongTerms.filter((term) => a.toLowerCase().includes(term)).length;
    const bScore = strongTerms.filter((term) => b.toLowerCase().includes(term)).length;
    return bScore - aScore || a.length - b.length;
  })[0];

  return {
    id: "user-statement",
    text: picked.replace(/^"|"$/g, ""),
    author: "From your answers",
    source: "user",
    evidence: "Verified from stored journey answers.",
  };
}

export function selectStrategicQuote({ context = "phase_intro", phaseId = 1, sourceText = "" } = {}) {
  const localSignal = collectLocalSignal(sourceText);
  const fullSource = [localSignal.text, sourceText].filter(Boolean).join("\n");
  const userQuote = extractUserQuote(fullSource, context);
  if (userQuote && context === "brand_book_page") return userQuote;

  const ranked = QUOTE_BANK
    .map((quote) => ({ quote, score: scoreQuote(quote, { context, phaseId, sourceText: fullSource }) }))
    .sort((a, b) => b.score - a.score);
  const topScore = ranked[0]?.score ?? 0;
  const finalists = ranked.filter((item) => item.score === topScore).map((item) => item.quote);
  const picked = finalists[sessionHash(`${localSignal.sessionId}:${context}:${phaseId}`) % Math.max(finalists.length, 1)] || ranked[0]?.quote || QUOTE_BANK[0];
  const matchedThemes = getEvidenceThemes(fullSource, picked.themes);

  return {
    ...picked,
    source: "curated",
    evidence: matchedThemes.length
      ? `Matched to ${matchedThemes.join(", ")} signals in the journey.`
      : "Selected for this strategic transition.",
  };
}

export function getPageSourceText(page) {
  if (!page || typeof page !== "object") return "";
  const parts = [page.title, page.statement];
  if (Array.isArray(page.sections)) {
    page.sections.forEach((section) => parts.push(section?.title, section?.content));
  }
  if (Array.isArray(page.dna_points)) parts.push(page.dna_points.join(" "));
  if (page.emotional_connection) {
    parts.push(page.emotional_connection.before, page.emotional_connection.after);
  }
  if (page.style_tone) {
    parts.push(page.style_tone.summary, page.style_tone.tone, page.style_tone.visual, page.style_tone.design);
  }
  if (Array.isArray(page.taglines)) parts.push(page.taglines.join(" "));
  return parts.filter(Boolean).join("\n");
}