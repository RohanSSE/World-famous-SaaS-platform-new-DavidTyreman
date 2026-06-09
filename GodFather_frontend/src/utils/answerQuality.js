/** Client-side mirror of backend answer quality labels (instant feedback while API loads). */

export const QUALITY_LABELS = {
  too_weak: "Good start — let’s give it more soul",
  vendor_thought: "Nice direction — let’s make it feel more ownable",
  strong: "This has a strong spark — let’s sharpen it",
};

const QUALITY_REASONS = {
  too_weak:
    "Acha start hai. Add one real feeling, one specific reason, or one behavior so it feels more memorable.",
  vendor_thought:
    "You’re on the right track. Let’s shift it from service language into belief, behavior, and emotional truth.",
  strong:
    "This already has something useful. A sharper detail or vivid moment can make it land even better.",
};

export function normalizeAnswerQualityCopy(raw = {}) {
  const quality = Object.prototype.hasOwnProperty.call(QUALITY_LABELS, raw.quality)
    ? raw.quality
    : "too_weak";
  const reason = String(raw.reason || "").trim().toLowerCase();
  let friendlyReason = raw.reason || QUALITY_REASONS[quality];

  if (
    !raw.reason ||
    reason.includes("too short") ||
    reason.includes("too weak") ||
    reason.includes("lacks") ||
    reason.includes("generic words") ||
    reason.includes("vendor pitch") ||
    reason.includes("transactional") ||
    reason.includes("not a brand truth")
  ) {
    friendlyReason = QUALITY_REASONS[quality];
  }

  return {
    ...raw,
    quality,
    quality_label: QUALITY_LABELS[quality],
    reason: friendlyReason,
  };
}

const GENERIC = new Set([
  "quality",
  "professional",
  "innovative",
  "solutions",
  "creative",
  "inspiring",
  "helpful",
  "reliable",
  "excellence",
  "leading",
]);

const VENDOR_RE = [
  /\bwe provide\b/i,
  /\bwe offer\b/i,
  /\bour services\b/i,
  /\bunmet (market )?needs\b/i,
  /\bmarket needs\b/i,
  /\bpractical solutions\b/i,
  /\baddress gaps\b/i,
  /\bhelp (businesses|companies|clients)\b/i,
  /\binnovative solutions\b/i,
];

const PHASE1_MIN_WORDS = [12, 11, 13, 12, 14, 10, 11, 13];

function wordCount(text) {
  return (text.match(/\b[\w']+\b/g) || []).length;
}

function getProfile(question) {
  const raw = question?.raw || question || {};
  const stage = Number(raw.stage) || 1;
  const order = Number(raw.order) ?? 0;
  const category = raw.category || "other";

  let minWords = stage === 2 ? 13 : stage === 3 ? 12 : 11;
  if (stage === 1 && PHASE1_MIN_WORDS[order] != null) {
    minWords = PHASE1_MIN_WORDS[order];
  } else if (category === "target_audience") minWords = 13;
  else if (category === "brand_identity") minWords = 12;

  return { stage, order, category, minWords };
}

/** Pull paste-ready answer text from AI coaching wrappers. */
export function extractApplicableNudgeText(raw) {
  let text = String(raw ?? "").trim();
  if (!text) return "";

  const likeQuoted = text.match(/\blike\s+['"]([^'"]+)['"]\s*\.?$/i);
  if (likeQuoted) return likeQuoted[1].trim();

  const wrappedQuote = text.match(/^['"](.+)['"]\s*\.?$/s);
  if (wrappedQuote) return wrappedQuote[1].trim();

  if (/^(rewrite|try|instead|consider|say|use|example|suggestion|you could)/i.test(text) && text.includes(":")) {
    const afterColon = text.split(":").slice(1).join(":").trim();
    const nested = extractApplicableNudgeText(afterColon);
    if (nested && nested.length < text.length) return nested;
  }

  text = text
    .replace(/^rewrite\s+with\s+[^,]+,\s*like\s+/i, "")
    .replace(/^try\s+this\s+instead:\s*/i, "")
    .replace(/^you\s+could\s+(also\s+)?say:\s*/i, "")
    .replace(/^instead,?\s+(try\s+)?/i, "")
    .trim();

  const trailingQuote = text.match(/^['"](.+)['"]\s*\.?$/s);
  if (trailingQuote) return trailingQuote[1].trim();

  return text;
}

export function scoreAnswerQualityLocal(question, text) {
  const draft = String(text || "").trim();
  const { minWords } = getProfile(question);
  const wc = wordCount(draft);
  const words = (draft.match(/\b[\w']+\b/g) || []).map((w) => w.toLowerCase());

  let vendorHits = 0;
  for (const re of VENDOR_RE) {
    if (re.test(draft)) vendorHits += 1;
  }

  const genericHits = words.filter((w) => GENERIC.has(w)).length;
  const genericDensity = words.length ? genericHits / words.length : 0;

  let quality = "strong";
  let reason = QUALITY_REASONS.strong;

  if (wc < Math.max(6, minWords - 4) || draft.length < 28) {
    quality = "too_weak";
    reason = `Acha start hai. Add a little more emotional truth and aim for around ${minWords} words.`;
  } else if (vendorHits >= 2 || (vendorHits >= 1 && genericDensity > 0.15)) {
    quality = "vendor_thought";
    reason = QUALITY_REASONS.vendor_thought;
  } else if (genericDensity >= 0.2 && wc < minWords) {
    quality = "too_weak";
    reason = "Good direction. Now replace broad words with a detail only your brand would say.";
  } else if (vendorHits >= 1 && wc < minWords + 2) {
    quality = "vendor_thought";
    reason = QUALITY_REASONS.vendor_thought;
  }

  return normalizeAnswerQualityCopy({
    quality,
    reason,
  });
}
