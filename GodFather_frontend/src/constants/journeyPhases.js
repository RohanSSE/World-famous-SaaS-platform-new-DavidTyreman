export const JOURNEY_PHASES = [
  {
    id: 1,
    questions: "Questions 1–8",
    title: "Foundation & Identity",
    description:
      "Discover the emotional truth, meaning, positioning, and opportunity behind your brand.",
    intro: {
      headline: "Phase 1: Who are you?",
      bodyLines: [
        "This is the beginning of a strategic conversation designed to uncover what makes your brand meaningful, differentiated, and memorable.",
        "The answers you give here will influence everything that follows.",
      ],
    },
    unlocked: true,
    complete: {
      title: "Phase 1 Completed",
      subtitle: "You've completed the first stage of discovery.",
      understandingTitle: "We now have a stronger understanding of:",
      bullets: [
        "your motivations",
        "emotional themes",
        "positioning patterns",
        "strategic opportunities worth exploring further",
      ],
      nextText:
        "The next phase will go deeper into differentiation, customer psychology, and strategic identity.",
      progressPercent: 25,
      ctaLabel: "Let's Go Deeper",
    },
  },
  {
    id: 2,
    questions: "Questions 9–20",
    title: "Differentiation & Strategic Depth",
    description:
      "Define what makes your brand emotionally meaningful, memorable, and difficult to ignore.",
    intro: {
      headline: "Phase 2: What makes you different?",
      bodyLines: [
        "Now we go deeper into what sets your brand apart — the emotional and strategic choices that make you memorable.",
        "This phase sharpens the strategic choices that are hard to ignore.",
      ],
    },
    unlocked: false,
    complete: {
      title: "Phase 2 Completed",
      subtitle: "You've completed the second stage of discovery.",
      understandingTitle: "We now have a stronger understanding of:",
      bullets: [
        "what makes you different",
        "customer psychology",
        "strategic identity choices",
        "how your brand stands apart",
      ],
      nextText:
        "The final phase will align everything into a clear Brand Book foundation.",
      progressPercent: 50,
      ctaLabel: "Let's Go Deeper",
    },
  },
  {
    id: 3,
    questions: "Questions 21–30",
    title: "Alignment & Brand Expansion",
    description:
      "Transform your insights into a strategically aligned Brand Book and long-term growth foundation.",
    intro: {
      headline: "Phase 3: Where are you going?",
      bodyLines: [
        "We align everything you've uncovered into a clear Brand Book.",
        "This foundation supports long-term brand growth.",
      ],
    },
    unlocked: false,
    complete: {
      title: "Discovery Complete!",
      subtitle: "You've answered all 30 questions. Your strategic brand book is ready to be generated.",
      understandingTitle: "",
      bullets: [],
      nextText: "",
      progressPercent: 100,
      ctaLabel: "Generate My Brand Book",
      minimal: true,
    },
  },
];

const UNLOCK_STORAGE_KEY = "journeyUnlockedPhases";

export function getUnlockedPhaseIds() {
  try {
    const raw = localStorage.getItem(UNLOCK_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [1];
    return Array.isArray(parsed) ? parsed.map(Number) : [1];
  } catch {
    return [1];
  }
}

export function isPhaseUnlocked(phaseId) {
  const id = Number(phaseId);
  if (id === 1) return true;
  if (id >= 2) {
    if (isPhaseSubscriptionLocked(id)) return false;
  }
  if (id === 2) return true;
  return getUnlockedPhaseIds().includes(id);
}

/** Unlock the next phase after completing `phaseId`. */
export function unlockPhaseAfterComplete(phaseId) {
  const next = Number(phaseId) + 1;
  if (next > JOURNEY_PHASES.length) return;
  const ids = new Set(getUnlockedPhaseIds());
  ids.add(next);
  localStorage.setItem(UNLOCK_STORAGE_KEY, JSON.stringify([...ids].sort((a, b) => a - b)));
}

export function getJourneyPhase(id) {
  return JOURNEY_PHASES.find((p) => p.id === Number(id));
}

/** Figma sidebar labels — Phase 1 manifesto (8 questions) */
export const PHASE_1_MANIFESTO_STEPS = [
  "Brand Attitude",
  "Brand Culture",
  "Originality Check",
  "Customer",
  "Legacy & Impact",
  "Brand Discipline",
  "Emotional Anchor",
  "Mapping",
];

// Frontend "Phase 1" UI expects the backend's stage=1 ("Basic") questions list.
// Backend: question_list() returns stage=1 questions when session.get_current_stage() === 1.
export const PHASE_FOUNDATION_STAGE = 1;

export const TOTAL_JOURNEY_QUESTIONS = 30;

export const JOURNEY_STAGE_QUESTION_COUNTS = {
  1: 8,
  2: 12,
  3: 10,
};

export function getStoredBillingUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "{}");
  } catch {
    return {};
  }
}

export function getSubscriptionGateAfter(source) {
  const plan = source?.plan || source?.subscription_plan || source?.active_subscription?.plan;
  const value = Number(plan?.question_gate_after);
  if (Number.isFinite(value)) return Math.max(0, Math.min(TOTAL_JOURNEY_QUESTIONS, value));
  return 8;
}

export function hasActiveSubscription(source) {
  return !!(source?.has_active_subscription || source?.active_subscription?.is_active);
}

export function getPhaseStartQuestion(phaseId) {
  let start = 1;
  for (let phase = 1; phase < Number(phaseId); phase += 1) {
    start += JOURNEY_STAGE_QUESTION_COUNTS[phase] || 0;
  }
  return start;
}

export function getJourneyQuestionNumber(phaseId, questionIndex) {
  return getPhaseStartQuestion(phaseId) + Number(questionIndex || 0);
}

export function isJourneyQuestionUnlocked(questionNumber, source = getStoredBillingUser()) {
  if (hasActiveSubscription(source)) return true;
  return Number(questionNumber) <= getSubscriptionGateAfter(source);
}

export function doesPhaseRequireSubscription(phaseId, source = getStoredBillingUser()) {
  return getPhaseStartQuestion(phaseId) > getSubscriptionGateAfter(source);
}

export function isPhaseSubscriptionLocked(phaseId, source = getStoredBillingUser()) {
  return doesPhaseRequireSubscription(phaseId, source) && !hasActiveSubscription(source);
}

export function getPhaseAnswersStorageKey(sessionId, phaseId) {
  return sessionId
    ? `phaseAnswers_${sessionId}_p${phaseId}`
    : `phaseAnswers_p${phaseId}`;
}

export function getCurrentQuestionStorageKey(sessionId, phaseId) {
  return sessionId
    ? `phaseCurrentQuestion_${sessionId}_p${phaseId}`
    : `phaseCurrentQuestion_p${phaseId}`;
}

export function resetActiveJourneyState() {
  try {
    localStorage.removeItem("session");
    localStorage.removeItem("sessionId");
    localStorage.setItem(UNLOCK_STORAGE_KEY, JSON.stringify([1]));

    for (let phase = 1; phase <= JOURNEY_PHASES.length; phase += 1) {
      localStorage.removeItem(getPhaseAnswersStorageKey(null, phase));
      localStorage.removeItem(getCurrentQuestionStorageKey(null, phase));
    }
  } catch {
    /* ignore localStorage failures */
  }
}

/** Count non-empty answers stored locally across all journey phases. */
export function countStoredJourneyAnswers(sessionId) {
  let total = 0;
  for (let phase = 1; phase <= JOURNEY_PHASES.length; phase += 1) {
    try {
      const raw = localStorage.getItem(getPhaseAnswersStorageKey(sessionId, phase));
      if (!raw) continue;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") continue;
      total += Object.values(parsed).filter((v) => String(v ?? "").trim()).length;
    } catch {
      /* ignore */
    }
  }
  return total;
}
