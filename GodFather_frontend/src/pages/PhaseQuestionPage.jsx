import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useNavigate, useParams, Navigate, useSearchParams } from "react-router-dom";
import { toast } from "react-toastify";
import { Menu, X } from "lucide-react";
import ChatNavbar from "./ChatNavbar";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import authService from "../services/authService";
import {
  getJourneyPhase,
  getJourneyQuestionNumber,
  getStoredBillingUser,
  isJourneyQuestionUnlocked,
  isPhaseUnlocked,
  JOURNEY_PHASES,
  unlockPhaseAfterComplete,
  PHASE_1_MANIFESTO_STEPS,
  countStoredJourneyAnswers,
  getCurrentQuestionStorageKey,
  getPhaseAnswersStorageKey,
} from "../constants/journeyPhases";
import chatIcon1 from "../assets/chat-icon1.png";
import chatIcon2 from "../assets/chat-icon2.png";
import {
  extractApplicableNudgeText,
  scoreAnswerQualityLocal,
} from "../utils/answerQuality";
import "./PhaseQuestionPage.css";

const BGF_HELP_ACTIONS = [
  { intent: "hint", label: "Hint" },
  { intent: "example", label: "Example" },
  { intent: "why", label: "Why it matters" },
  { intent: "explain", label: "Explain" },
  { intent: "context", label: "Context" },
];

// Temporarily hidden until the client approves the expanded Ask BGF helper.
const SHOW_BGF_HELP_PANEL = false;
const LEGACY_RAG_V1_DISABLED = true;
const LEGACY_RAG_V2_DISABLED = true;
// Older expanded ORB Intelligence debug card is hidden for now; use the API response link instead.
const SHOW_LEGACY_ORB_INTELLIGENCE_PANEL = false;

function resolveOrbQuestionId(question, questionIndex, phaseId) {
  const rawId = question?.raw?.q_id || question?.raw?.brandgodfather_q_id;
  if (rawId) {
    const normalized = String(rawId).trim();
    return normalized.toUpperCase().startsWith("Q") ? normalized.toUpperCase() : `Q${normalized}`;
  }

  const order = Number(question?.raw?.order ?? question?.order);
  if (Number.isFinite(order) && order > 0) return `Q${order}`;

  const phaseNumber = Number(phaseId) || 1;
  const fallbackOffset = phaseNumber === 1 ? 0 : (phaseNumber - 1) * 10;
  return `Q${fallbackOffset + Number(questionIndex ?? 0) + 1}`;
}

function splitFollowUp(text) {
  const value = String(text || "").trim();
  if (!value.includes("?")) return { statement: value, followUp: "" };
  const chunks = value.split(/(?<=[.!?])\s+/);
  let qIdx = -1;
  chunks.forEach((chunk, idx) => {
    if (chunk.trim().endsWith("?")) qIdx = idx;
  });
  if (qIdx < 0) return { statement: value, followUp: "" };
  const statement = chunks.slice(0, qIdx).join(" ").trim();
  const followUp = chunks.slice(qIdx).join(" ").trim();
  return { statement, followUp };
}

function normalizeOrbResult(orbResult) {
  const status = String(orbResult?.status || "UNKNOWN").toUpperCase();
  const isNewOrbResult = Boolean(
    orbResult?.associated_discovery_id ||
      orbResult?.target_confidence_threshold != null ||
      orbResult?.confidence_score != null ||
      orbResult?.advance_to_next_question != null,
  );
  const blockedPhrases = Array.isArray(orbResult?.blocked_phrases)
    ? orbResult.blocked_phrases.filter(Boolean)
    : [];
  const rawReply = String(
    orbResult?.reply || orbResult?.response || orbResult?.follow_up_question || "Let's go deeper before we move on.",
  ).trim();
  let followUp = String(
    status === "INCOMPLETE" ? orbResult?.follow_up_question || orbResult?.response || "" : orbResult?.follow_up_question || "",
  ).trim();
  let statement = rawReply;
  if (isNewOrbResult && status === "COMPLETE") {
    followUp = "";
  } else if (followUp) {
    const parts = splitFollowUp(rawReply);
    if (parts.followUp) statement = parts.statement || rawReply;
  } else {
    const parts = splitFollowUp(rawReply);
    if (parts.statement) {
      statement = parts.statement;
      followUp = parts.followUp;
    }
  }
  return {
    status,
    reply: statement,
    raw_reply: rawReply,
    follow_up_question: followUp,
    next_q_id: orbResult?.next_q_id || (orbResult?.advance_to_next_question ? "Next question" : "Awaiting stronger answer"),
    depth_score: orbResult?.depth_score ?? orbResult?.confidence_score ?? "not scored",
    interruption_type: orbResult?.interruption_type || null,
    challenge_type: orbResult?.challenge_type || orbResult?.associated_discovery_id || null,
    pressure_used: orbResult?.pressure_used ?? null,
    resistance_count: orbResult?.resistance_count ?? 0,
    emotional_state: orbResult?.emotional_state || "neutral",
    tone_mode: orbResult?.tone_mode || "direct_challenge",
    blocked_phrases: blockedPhrases,
    prosody_flags: Array.isArray(orbResult?.prosody_flags) ? orbResult.prosody_flags : [],
    contradiction_result: orbResult?.contradiction_result || null,
    contradiction_message: orbResult?.contradiction_message || null,
    breakthrough_detected: Boolean(orbResult?.breakthrough_detected),
    breakthrough_score: orbResult?.breakthrough_score ?? orbResult?.confidence_score ?? 0,
    breakthrough_type: orbResult?.breakthrough_type || null,
    breakthrough_reason: orbResult?.breakthrough_reason || null,
    breakthrough_seed: orbResult?.breakthrough_seed || null,
    breakthrough_criteria: orbResult?.breakthrough_criteria || {},
    sessionId: orbResult?.brandgodfather_session_id || null,
    associated_discovery_id: orbResult?.associated_discovery_id || null,
    target_confidence_threshold: orbResult?.target_confidence_threshold ?? orbResult?.metadata?.target_confidence_threshold ?? null,
    metadata: orbResult?.metadata || null,
    crux_context: orbResult?.crux_context || null,
    confidence_tracking: orbResult?.confidence_tracking || orbResult?.view_api_response?.data?.confidence_tracking || null,
    view_api_response: orbResult?.view_api_response || null,
    confidence_score: orbResult?.confidence_score ?? null,
    extracted_signals: orbResult?.extracted_signals || {},
    advance_to_next_question: Boolean(orbResult?.advance_to_next_question || status === "COMPLETE"),
  };
}

function SessionTitleModal({
  open,
  title,
  onTitleChange,
  agencies,
  selectedAgency,
  onAgencyChange,
  agenciesLoading,
  agenciesError,
  showAgencyPicker,
  onSubmit,
  loading,
  error,
}) {
  if (!open) return null;
  return (
    <div className="pq-modal-overlay">
      <div className="pq-modal">
        <h2>Name your session</h2>
        <p>Give this brand journey a title before we begin.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="e.g. Acme Brand Discovery"
            autoFocus
          />
          {showAgencyPicker && (
            <>
              <label className="pq-modal-label" htmlFor="pq-agency-select">
                Agency
              </label>
              <select
                id="pq-agency-select"
                className="pq-modal-select"
                value={selectedAgency}
                onChange={(e) => onAgencyChange(e.target.value)}
                disabled={agenciesLoading}
              >
                <option value="0">No agency</option>
                {agencies.map((a) => {
                  const id = a.id ?? a.pk;
                  return (
                    <option key={id} value={id}>
                      {a.name || a.title || `Agency ${id}`}
                    </option>
                  );
                })}
              </select>
              {agenciesError && <p className="pq-modal-hint">{agenciesError}</p>}
            </>
          )}
          {error && <p className="pq-modal-error">{error}</p>}
          <button type="submit" disabled={loading || !title.trim()}>
            {loading ? "Creating…" : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function PhaseQuestionPage() {
  const navigate = useNavigate();
  const { phaseId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const phase = getJourneyPhase(phaseId);
  const inputRef = useRef(null);

  const resizeInput = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${el.scrollHeight}px`;
  };

  const savedSessionJson = localStorage.getItem("session");
  const savedSessionId = localStorage.getItem("sessionId");
  const initialSession = savedSessionJson
    ? JSON.parse(savedSessionJson)
    : savedSessionId
      ? { id: savedSessionId }
      : null;

  const [session, setSession] = useState(initialSession);
  const sessionId = (session && (session.id || session.pk)) || savedSessionId;

  const [showTitleModal, setShowTitleModal] = useState(!initialSession);
  const [modalTitle, setModalTitle] = useState("");
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");
  const [agencies, setAgencies] = useState([]);
  const [selectedAgency, setSelectedAgency] = useState("0");
  const [agenciesLoading, setAgenciesLoading] = useState(false);
  const [agenciesError, setAgenciesError] = useState("");

  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(!!initialSession);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [nudges, setNudges] = useState([]);
  const [nudgeQuality, setNudgeQuality] = useState(null);
  const [, setNudgeQuote] = useState(null);
  const [nudgeIndex, setNudgeIndex] = useState(0);
  const [nudgesLoading, setNudgesLoading] = useState(false);
  const [orbVerdict, setOrbVerdict] = useState(null);
  const [orbChecking, setOrbChecking] = useState(false);
  const [livePreview, setLivePreview] = useState(null);
  const [livePreviewChecking, setLivePreviewChecking] = useState(false);
  const [showApiData, setShowApiData] = useState(false);
  const [nudgesFading, setNudgesFading] = useState(false);
  const [replyVisible, setReplyVisible] = useState(false);
  const [bgfHelpLoading, setBgfHelpLoading] = useState(false);
  const [bgfHelpResponse, setBgfHelpResponse] = useState(null);
  const [bgfAskText, setBgfAskText] = useState("");
  const [, setJourneyAnsweredCount] = useState(0);
  const [billing, setBilling] = useState(null);
  const [billingLoading, setBillingLoading] = useState(false);
  const [billingError, setBillingError] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [answerReward, setAnswerReward] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const nudgesDebounceRef = useRef(null);
  const nudgePickedRef = useRef(false);
  const livePreviewDebounceRef = useRef(null);
  const livePreviewAbortRef = useRef(null);
  const livePreviewSeqRef = useRef(0);
  const replyRevealTimersRef = useRef([]);
  const currentInputAiDraftRef = useRef(false);
  const answerRewardTimeoutRef = useRef(null);
  const questionIndexRestoredRef = useRef(false);
  const shouldForceQuestionRefineRef = useRef(
    typeof performance !== "undefined" &&
      performance.getEntriesByType?.("navigation")?.[0]?.type === "reload",
  );
  const currentUser = authService.getCurrentUser() || {};
  const isAgencyUser = currentUser.role === 3 || currentUser.role_name === "agency";

  const storageKey = getPhaseAnswersStorageKey(sessionId, phaseId);
  const currentQuestionStorageKey = getCurrentQuestionStorageKey(sessionId, phaseId);

  useEffect(() => {
    questionIndexRestoredRef.current = false;
    setCurrentIdx(0);
  }, [currentQuestionStorageKey]);

  useEffect(() => {
    if (session) setShowTitleModal(false);
  }, [session]);

  useEffect(() => {
    return () => window.clearTimeout(answerRewardTimeoutRef.current);
  }, []);

  useEffect(() => {
    if (!sidebarOpen) return undefined;
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [sidebarOpen]);

  useEffect(() => {
    let cancelled = false;
    async function loadBilling() {
      setBillingLoading(true);
      setBillingError("");
      try {
        const checkoutSessionId = searchParams.get("session_id");
        const checkoutStatus = searchParams.get("checkout");
        const data =
          checkoutStatus === "success" && checkoutSessionId
            ? await authService.verifySubscriptionCheckout(checkoutSessionId)
            : await authService.getBillingStatus();

        if (cancelled) return;
        setBilling(data);
        if (checkoutStatus) setSearchParams({}, { replace: true });
      } catch (err) {
        if (!cancelled) setBillingError(err?.message || "Could not load subscription");
      } finally {
        if (!cancelled) setBillingLoading(false);
      }
    }

    loadBilling();
    return () => {
      cancelled = true;
    };
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (!showTitleModal) return;
    if (isAgencyUser) {
      setAgencies([]);
      setSelectedAgency("0");
      setAgenciesError("");
      return;
    }
    let cancelled = false;
    (async () => {
      setAgenciesLoading(true);
      setAgenciesError("");
      try {
        const list = await authService.getAgencies();
        if (cancelled) return;
        const normalized = Array.isArray(list) ? list : [];
        setAgencies(normalized);
        if (normalized.length > 0) {
          const id = normalized[0].id ?? normalized[0].pk ?? 0;
          setSelectedAgency(String(id));
        }
      } catch (err) {
        if (!cancelled) setAgenciesError(err?.message || "Could not load agencies");
      } finally {
        if (!cancelled) setAgenciesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [showTitleModal, isAgencyUser]);

  useEffect(() => {
    if (initialSession || session) return;
    let cancelled = false;
    (async () => {
      try {
        let list = [];
        try {
          const currentUser = authService.getCurrentUser() || {};
          const isAgencyUser = currentUser.role === 3 || currentUser.role_name === "agency";
          if (isAgencyUser) {
            const dashboard = await authService.getUserDashboard();
            list = Array.isArray(dashboard?.sessions) ? dashboard.sessions : [];
          } else {
            list = await authService.getSessions();
          }
        } catch {
          list = await authService.getSessions();
        }
        if (cancelled) return;
        const draft = (Array.isArray(list) ? list : []).find(
          (s) => s.status === "draft" || s.status === "in_progress",
        );
        if (draft) {
          localStorage.setItem("session", JSON.stringify(draft));
          if (draft.id) localStorage.setItem("sessionId", String(draft.id));
          setSession(draft);
          setShowTitleModal(false);
        }
      } catch {
        /* show title modal */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initialSession, session]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) setAnswers(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, [storageKey]);

  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }
    let cancelled = false;

    async function loadQuestions() {
      setLoading(true);
      setLoadError("");
      try {
        const targetStage = Number(phaseId) || 1;
        const res = await authService.getQuestions(sessionId, targetStage, {
          forceRefine: shouldForceQuestionRefineRef.current,
        });
        shouldForceQuestionRefineRef.current = false;
        if (cancelled) return;
        let all = Array.isArray(res) ? res : res?.questions || (res?.question ? [res.question] : []);
        all = all
          .filter((q) => String(q.stage) === String(targetStage))
          .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

        const mapped = all.map((q, i) => ({
          id: q.id,
          key: `q_${q.id}`,
          text: q.user_facing_text || q.ai_refined_text || q.text || q.title || `Question ${i + 1}`,
          placeholder: q.placeholder || "Type your answer…",
          raw: q,
          shortLabel:
            Number(phaseId) === 1 ? PHASE_1_MANIFESTO_STEPS[i] || `Step ${i + 1}` : `Step ${i + 1}`,
        }));

        if (!cancelled) setQuestions(mapped);
      } catch (err) {
        if (!cancelled) setLoadError(err?.message || "Failed to load questions");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadQuestions();
    return () => {
      cancelled = true;
    };
  }, [sessionId, phaseId]);

  useEffect(() => {
    if (!questions.length || questionIndexRestoredRef.current) return;
    questionIndexRestoredRef.current = true;

    try {
      const savedIndex = Number(localStorage.getItem(currentQuestionStorageKey));
      if (Number.isFinite(savedIndex)) {
        setCurrentIdx(Math.max(0, Math.min(questions.length - 1, savedIndex)));
      }
    } catch {
      /* keep first question */
    }
  }, [currentQuestionStorageKey, questions.length]);

  useEffect(() => {
    if (!questions.length || !questionIndexRestoredRef.current) return;
    try {
      localStorage.setItem(currentQuestionStorageKey, String(currentIdx));
    } catch {
      /* ignore */
    }
  }, [currentIdx, currentQuestionStorageKey, questions.length]);

  useEffect(() => {
    if (!sessionId || questions.length === 0) return;
    let cancelled = false;

    async function loadExistingAnswers() {
      try {
        const remoteAnswers = await authService.getAnswers(sessionId, {});
        if (cancelled) return;

        const idToKey = {};
        questions.forEach((q) => {
          const qid = q.raw?.id ?? q.id;
          if (qid != null) idToKey[String(qid)] = q.key;
        });

        const localAnswers = JSON.parse(localStorage.getItem(storageKey) || "{}");
        const next = localAnswers && typeof localAnswers === "object" ? { ...localAnswers } : {};
        (Array.isArray(remoteAnswers) ? remoteAnswers : []).forEach((a) => {
          const key = idToKey[String(a.question)] || `q_${a.question}`;
          if (typeof a.answer_text === "string" && a.answer_text.trim() !== "") {
            next[key] = a.answer_text;
          }
        });
        localStorage.setItem(storageKey, JSON.stringify(next));
        setAnswers(next);
        setJourneyAnsweredCount(countStoredJourneyAnswers(sessionId));
      } catch {
        /* keep local cache */
      }
    }

    loadExistingAnswers();
    return () => {
      cancelled = true;
    };
  }, [sessionId, questions, storageKey]);

  useEffect(() => {
    setJourneyAnsweredCount(countStoredJourneyAnswers(sessionId));
  }, [sessionId]);

  useEffect(() => {
    const q = questions[currentIdx];
    if (!q) return;
    const saved = answers[q.key];
    currentInputAiDraftRef.current = false;
    setInputValue(saved != null ? String(saved) : "");
    setNudges([]);
    setNudgeQuality(null);
    setNudgeQuote(null);
    setOrbVerdict(null);
    setOrbChecking(false);
    setLivePreview(null);
    setLivePreviewChecking(false);
    livePreviewSeqRef.current += 1;
    if (livePreviewDebounceRef.current) clearTimeout(livePreviewDebounceRef.current);
    if (livePreviewAbortRef.current) livePreviewAbortRef.current.abort();
    setNudgeIndex(0);
    setNudgesLoading(false);
    setBgfHelpResponse(null);
    setBgfAskText("");
    setBgfHelpLoading(false);
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.focus();
    }
  }, [currentIdx, questions, answers]);

  useLayoutEffect(() => {
    resizeInput();
  }, [inputValue, currentIdx]);

  // Real-time ORB verdict while the user types (read-only dry-run, debounced).
  useEffect(() => {
    if (livePreviewDebounceRef.current) clearTimeout(livePreviewDebounceRef.current);

    if (LEGACY_RAG_V1_DISABLED) {
      setLivePreview(null);
      setLivePreviewChecking(false);
      if (livePreviewAbortRef.current) livePreviewAbortRef.current.abort();
      return;
    }

    const q = questions[currentIdx];
    const value = inputValue.trim();
    const MIN_PREVIEW_LEN = 12;

    // Don't preview while a real submit is in-flight or after a committed verdict.
    if (!sessionId || !q || submitting || orbChecking || value.length < MIN_PREVIEW_LEN) {
      setLivePreview(null);
      setLivePreviewChecking(false);
      if (livePreviewAbortRef.current) livePreviewAbortRef.current.abort();
      return;
    }

    livePreviewDebounceRef.current = setTimeout(async () => {
      if (livePreviewAbortRef.current) livePreviewAbortRef.current.abort();
      const controller = new AbortController();
      livePreviewAbortRef.current = controller;
      const seq = ++livePreviewSeqRef.current;

      setLivePreviewChecking(true);
      try {
        /* Legacy RAG v1 live preview disabled while Phase 1 uses edit_conversation ORB.
        const orbQId = resolveOrbQuestionId(q, currentIdx, phaseId);
        const res = await authService.previewBrandGodFatherAnswer({
          sourceSessionId: sessionId,
          qId: orbQId,
          answer: value,
          contextData: {
            frontend_page: "PhaseQuestionPage",
            phase_id: phaseId,
            question_id: q.raw?.id ?? q.id,
            question_text: q.text,
            question_bank: { [orbQId]: q.text },
            live_preview: true,
          },
          signal: controller.signal,
        });
        // Ignore stale/cancelled responses.
        if (seq !== livePreviewSeqRef.current) return;
        setLivePreview(res ? normalizeOrbResult(res) : null);
        */
        if (seq !== livePreviewSeqRef.current) return;
        setLivePreview(null);
      } catch {
        if (seq === livePreviewSeqRef.current) setLivePreview(null);
      } finally {
        if (seq === livePreviewSeqRef.current) setLivePreviewChecking(false);
      }
    }, 800);

    return () => {
      if (livePreviewDebounceRef.current) clearTimeout(livePreviewDebounceRef.current);
    };
  }, [inputValue, currentIdx, questions, sessionId, phaseId, submitting, orbChecking]);

  // Staged reveal: show nudges ~2s, dissolve, then reveal the Brand Godfather reply.
  useEffect(() => {
    const verdict = orbVerdict || livePreview;
    const checking = orbChecking || (livePreviewChecking && !livePreview);
    const reply = !checking && verdict?.reply ? verdict.reply : null;

    replyRevealTimersRef.current.forEach(clearTimeout);
    replyRevealTimersRef.current = [];

    if (!reply) {
      setNudgesFading(false);
      setReplyVisible(false);
      return;
    }

    setReplyVisible(false);
    setNudgesFading(false);
    const t1 = setTimeout(() => setNudgesFading(true), 2000);
    const t2 = setTimeout(() => setReplyVisible(true), 2450);
    replyRevealTimersRef.current = [t1, t2];

    return () => {
      replyRevealTimersRef.current.forEach(clearTimeout);
      replyRevealTimersRef.current = [];
    };
  }, [orbVerdict, livePreview, orbChecking, livePreviewChecking]);

  const fetchNudges = async (hint, question) => {
    const q = question || questions[currentIdx];
    if (!q) return;

    if (LEGACY_RAG_V2_DISABLED) {
      setNudgeQuality(scoreAnswerQualityLocal(q, hint));
      setNudges([]);
      setNudgeQuote(null);
      setNudgeIndex(0);
      setNudgesLoading(false);
      return;
    }

    setNudgesLoading(true);
    setNudgeQuality(scoreAnswerQualityLocal(q, hint));

    try {
      /* Legacy RAG v2 answer suggestions disabled while Phase 1 uses edit_conversation ORB.
      const res = await authService.getAiAnswerSuggestions(sessionId, q.id, hint, { intent: "refine" });
      let list = [];
      if (Array.isArray(res)) {
        list = res;
      } else if (res && typeof res === "object") {
        list = res.suggestions ?? res.suggestion ?? [];
        setNudgeQuote(res.suggestion_quote?.enabled ? res.suggestion_quote : null);
        if (res.quality || res.reason) {
          setNudgeQuality(normalizeAnswerQualityCopy({
            quality: res.quality,
            quality_label: res.quality_label || "",
            reason: res.reason || "",
          }));
        }
      }
      const cleaned = (Array.isArray(list) ? list : [])
        .map((s) => extractApplicableNudgeText(String(s).trim()))
        .filter(Boolean);
      setNudges(cleaned);
      */
      setNudges([]);
      setNudgeIndex(0);
    } catch {
      setNudges([]);
      setNudgeQuote(null);
      setNudgeIndex(0);
    } finally {
      setNudgesLoading(false);
    }
  };

  // Live nudges while typing (debounced AI suggestions)
  useEffect(() => {
    if (nudgePickedRef.current) {
      nudgePickedRef.current = false;
      return;
    }

    if (nudgesDebounceRef.current) {
      clearTimeout(nudgesDebounceRef.current);
    }

    const q = questions[currentIdx];
    const hint = inputValue.trim();

    if (!sessionId || !q?.id || hint.length < 3) {
      setNudges([]);
      setNudgeQuality(null);
      setNudgeQuote(null);
      setNudgesLoading(false);
      return;
    }

    setNudgeQuality(scoreAnswerQualityLocal(q, hint));

    nudgesDebounceRef.current = setTimeout(async () => {
      if (nudgePickedRef.current) {
        nudgePickedRef.current = false;
        return;
      }
      await fetchNudges(hint, q);
    }, 500);

    return () => {
      if (nudgesDebounceRef.current) clearTimeout(nudgesDebounceRef.current);
    };
  }, [inputValue, currentIdx, questions, sessionId]);

  const applyNudge = (text) => {
    nudgePickedRef.current = true;
    currentInputAiDraftRef.current = true;
    const cleaned = extractApplicableNudgeText(text);
    setInputValue(cleaned);
    setNudgeQuote(null);
    setNudgeIndex(0);
    requestAnimationFrame(() => {
      resizeInput();
      inputRef.current?.focus();
    });
  };

  const handleRefineClick = async () => {
    const q = questions[currentIdx];
    const hint = inputValue.trim();
    if (!sessionId || !q?.id || hint.length < 3) return;

    if (nudges.length > 1) {
      setNudgeIndex((prev) => (prev + 1) % nudges.length);
      return;
    }
    await fetchNudges(hint, q);
  };

  const handleBgfHelp = async (intent, customQuestion = "") => {
    const q = questions[currentIdx];
    if (!sessionId || !q?.id || bgfHelpLoading) return;
    const trimmedQuestion = customQuestion.trim();
    if (intent === "ask" && !trimmedQuestion) return;

    if (nudgesDebounceRef.current) clearTimeout(nudgesDebounceRef.current);
    setBgfHelpLoading(true);
    setBgfHelpResponse(null);
    try {
      if (LEGACY_RAG_V2_DISABLED) {
        setBgfHelpResponse({
          title: "Brand Godfather",
          answer: "ORB now evaluates this answer when you submit it.",
        });
        return;
      }
      /* Legacy RAG v2 helper disabled while Phase 1 uses edit_conversation ORB.
      const res = await authService.getAiAnswerSuggestions(sessionId, q.id, inputValue.trim(), {
        intent,
        customQuestion: trimmedQuestion,
      });
      setBgfHelpResponse(res);
      */
      if (intent === "ask") setBgfAskText("");
    } catch (err) {
      setBgfHelpResponse({
        title: "Brand Godfather",
        answer: err?.message || "Could not answer that right now.",
      });
    } finally {
      setBgfHelpLoading(false);
    }
  };

  const persistAnswers = (next) => {
    setAnswers(next);
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      /* ignore */
    }
    setJourneyAnsweredCount(countStoredJourneyAnswers(sessionId));
  };

  const persistViewApiResponsePayload = (payload) => {
    if (!payload) return;
    try {
      const storagePayload = {
        saved_at: new Date().toISOString(),
        session_id: sessionId || null,
        phase_id: Number(phaseId) || 1,
        question_index: currentIdx + 1,
        question_id: currentQuestion?.raw?.id ?? currentQuestion?.id ?? null,
        payload,
      };
      const serialized = JSON.stringify(storagePayload);
      const scopedKey = `orbViewApiResponse:${sessionId || "no-session"}:p${Number(phaseId) || 1}:q${currentIdx + 1}`;
      localStorage.setItem("orbViewApiResponse:last", serialized);
      localStorage.setItem(scopedKey, serialized);
      sessionStorage.setItem("orbViewApiResponse:last", serialized);
      sessionStorage.setItem(scopedKey, serialized);
    } catch {
      /* ignore storage failures */
    }
  };

  const handleCreateSession = async () => {
    setModalError("");
    if (!modalTitle.trim()) return;

    const token = localStorage.getItem("accessToken");
    if (!token) {
      setModalError("Please log in again to create a session.");
      return;
    }

    setModalLoading(true);
    try {
      const agencyNum = isAgencyUser ? 0 : Number(selectedAgency) || 0;
      const data = await authService.createSession({
        title: modalTitle.trim(),
        agency: agencyNum > 0 ? agencyNum : undefined,
      });
      const sessionObj = data?.session || data;
      if (!sessionObj?.id && !sessionObj?.pk) {
        throw { message: "Session created but invalid response from server." };
      }
      localStorage.setItem("session", JSON.stringify(sessionObj));
      localStorage.setItem("sessionId", String(sessionObj.id ?? sessionObj.pk));
      setSession(sessionObj);
      setShowTitleModal(false);

      if (sessionObj.status === "draft" && sessionObj.id) {
        try {
          await authService.startSession(sessionObj.id);
        } catch {
          /* non-fatal */
        }
      }

      /* Legacy RAG v1 BrandGodFather session start disabled while Phase 1 uses edit_conversation ORB.
      try {
        const sourceSessionId = String(sessionObj.id ?? sessionObj.pk);
        await authService.ensureBrandGodFatherSession({
          sourceSessionId,
          contextData: {
            frontend_page: "PhaseQuestionPage",
            phase_id: 1,
            orb_journey_start: true,
          },
        });
      } catch {
        // non-fatal: answer submission will retry ORB session start
      }
      */
      navigate("/phase-intro/1");
    } catch (err) {
      setModalError(err?.message || "Failed to create session");
    } finally {
      setModalLoading(false);
    }
  };

  const allPhaseAnswered =
    questions.length > 0 &&
    questions.every((q) => String(answers[q.key] ?? "").trim());

  const isFinalPhase = Number(phaseId) === 3;

  const triggerAnswerReward = (phaseComplete = false, savedCount = 0) => {
    window.clearTimeout(answerRewardTimeoutRef.current);
    setAnswerReward({
      id: Date.now(),
      title: phaseComplete ? "Boss cleared" : "+120 XP",
      text: phaseComplete ? "All answers locked. Complete the level now." : "Clarity +1 · Originality +1",
      streak: Math.max(1, savedCount),
    });
    answerRewardTimeoutRef.current = window.setTimeout(() => {
      setAnswerReward(null);
    }, 1700);
  };

  const findLatestUserConversation = (items) => {
    const userMessages = (Array.isArray(items) ? items : [])
      .filter((item) => item?.role === "user")
      .sort((a, b) => {
        const aTime = new Date(a.created_at || 0).getTime();
        const bTime = new Date(b.created_at || 0).getTime();
        if (aTime !== bTime) return aTime - bTime;
        return Number(a.id || 0) - Number(b.id || 0);
      });
    return userMessages[userMessages.length - 1] || null;
  };

  const evaluateCurrentAnswerWithOrb = async (currentQuestion, value) => {
    const sid = sessionId;
    const apiQuestionId = currentQuestion.raw?.id ?? currentQuestion.id;
    if (!sid || !apiQuestionId) {
      throw new Error("Missing session or question for ORB evaluation");
    }

    // Append this reply as a new user turn so ORB can evaluate the full episode:
    // User answer -> ORB counter-question -> User follow-up reply.
    await authService.aiSuggestionDraft(sid, apiQuestionId, value, false);
    const conversations = await authService.getConversations(sid, apiQuestionId);
    const userConversation = findLatestUserConversation(conversations);

    if (!userConversation?.id) {
      throw new Error("Could not create an ORB conversation for this answer");
    }

    const orbQId = resolveOrbQuestionId(currentQuestion, currentIdx, phaseId);
    return authService.editConversation(sid, userConversation.id, {
      content: value,
      questionText: currentQuestion.text,
      contextData: {
        frontend_page: "PhaseQuestionPage",
        phase_id: phaseId,
        q_id: orbQId,
        question_id: apiQuestionId,
        question_text: currentQuestion.text,
        question_bank: { [orbQId]: currentQuestion.text },
      },
    });
  };

  const saveCurrentAnswer = async ({ waitForServer = true } = {}) => {
    const currentQuestion = questions[currentIdx];
    if (!currentQuestion) return null;
    const value = inputValue.trim();
    if (!value) {
      setSubmitError("Please answer before submitting.");
      return null;
    }
    setSubmitError("");

    setOrbChecking(true);
    setOrbVerdict(null);

    let orb;
    try {
      /* Legacy RAG v1 BrandGodFather submit disabled while Phase 1 uses edit_conversation ORB.
      const orbQId = resolveOrbQuestionId(currentQuestion, currentIdx, phaseId);
      const orbResponse = await authService.submitBrandGodFatherAnswer({
        sourceSessionId: sessionId,
        qId: orbQId,
        answer: value,
        contextData: {
          frontend_page: "PhaseQuestionPage",
          phase_id: phaseId,
          question_id: currentQuestion.raw?.id ?? currentQuestion.id,
          question_text: currentQuestion.text,
          question_bank: {
            [orbQId]: currentQuestion.text,
          },
        },
      });
      */
      const orbResponse = await evaluateCurrentAnswerWithOrb(currentQuestion, value);
      console.log("ORB metadata", orbResponse?.metadata || null);
      console.log("ORB target_confidence_threshold", orbResponse?.target_confidence_threshold ?? orbResponse?.metadata?.target_confidence_threshold ?? null);
      console.log("ORB crux_context", orbResponse?.crux_context || null);
      console.log("ORB confidence_tracking", orbResponse?.view_api_response?.data?.confidence_tracking || orbResponse?.confidence_tracking || null);
      orb = normalizeOrbResult(orbResponse);
      setOrbVerdict(orb);
    } catch (err) {
      const fallback = {
        status: "UNAVAILABLE",
        reply: err?.message || "ORB engine unavailable. Please try again when the backend is ready.",
        next_q_id: "ORB retry required",
        depth_score: "not scored",
      };
      setOrbVerdict(fallback);
      setSubmitError(fallback.reply);
      throw err;
    } finally {
      setOrbChecking(false);
    }

    if (orb.status === "INCOMPLETE") {
      setSubmitError("");
      return null;
    }

    if (orb.status !== "COMPLETE") {
      setSubmitError("ORB could not confirm this answer yet. Please try again.");
      return null;
    }

    const nextAnswers = { ...answers, [currentQuestion.key]: value };
    persistAnswers(nextAnswers);

    const sid = sessionId;
    const apiQuestionId = currentQuestion.raw?.id ?? currentQuestion.id;

    if (sid && apiQuestionId) {
      const wasAiAccepted = currentInputAiDraftRef.current;
      const savePromise = authService.createAnswer(sid, {
        question: Number(apiQuestionId),
        answer_text: value,
        frontend_phase: Number(phaseId) || 1,
        is_ai_accepted: wasAiAccepted,
        ai_suggestion: wasAiAccepted ? value : undefined,
      });
      if (waitForServer) {
        await savePromise;
      } else {
        savePromise.catch((err) => {
          setSubmitError(err?.message || "Answer saved locally. Server sync failed.");
        });
      }
    }
    currentInputAiDraftRef.current = false;
    return nextAnswers;
  };

  const handleSend = async () => {
    if (submitting) return;
    if (nudgesDebounceRef.current) clearTimeout(nudgesDebounceRef.current);
    setNudges([]);
    setNudgeQuote(null);
    setSubmitting(true);
    try {
      const nextAnswers = await saveCurrentAnswer({ waitForServer: false });
      if (!nextAnswers) return;

      const phaseComplete =
        questions.length > 0 &&
        questions.every((q) => String(nextAnswers[q.key] ?? "").trim());

      const savedCount = questions.filter((q) => String(nextAnswers[q.key] ?? "").trim()).length;
      triggerAnswerReward(phaseComplete, savedCount);

      if (!phaseComplete && currentIdx < questions.length - 1) {
        setCurrentIdx((i) => i + 1);
      }
    } catch (err) {
      setSubmitError(err?.message || "Failed to save answer");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendClick = () => {
    if (allPhaseAnswered) {
      toast.info("Hit submit button");
      return;
    }
    handleSend();
  };

  const handlePhaseSubmit = async () => {
    if (!allPhaseAnswered || submitting) return;
    setSubmitting(true);
    try {
      const currentQuestion = questions[currentIdx];
      const value = inputValue.trim();
      if (currentQuestion && value && !String(answers[currentQuestion.key] ?? "").trim()) {
        const saved = await saveCurrentAnswer();
        if (!saved) return;
      }

      if (Number(phaseId) > 1) {
        unlockPhaseAfterComplete(phaseId);
      }
      const completedPhase = getJourneyPhase(phaseId);
      if (completedPhase?.complete) {
        navigate(`/phase-complete/${phaseId}`);
        return;
      }
      navigate("/ChatKickoffPage");
    } catch (err) {
      setSubmitError(err?.message || "Failed to complete phase");
    } finally {
      setSubmitting(false);
    }
  };

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx((i) => i - 1);
  };

  const handleNextNav = () => {
    if (currentIdx < questions.length - 1) setCurrentIdx((i) => i + 1);
  };

  const handleSubmitClick = () => {
    if (isFinalPhase && allPhaseAnswered) {
      toast.info("Hit save button");
      return;
    }
    handlePhaseSubmit();
  };

  const handleQuestionUpgrade = async () => {
    if (checkoutLoading) return;
    setCheckoutLoading(true);
    setBillingError("");
    try {
      const origin = window.location.origin;
      const data = await authService.createSubscriptionCheckout({
        success_url: `${origin}/phase-questions/${phaseId}?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${origin}/phase-questions/${phaseId}?checkout=cancel`,
      });
      if (data?.already_active) {
        setBilling(data);
        return;
      }
      if (!data?.checkout_url) throw new Error("Checkout URL missing from server response");
      window.location.href = data.checkout_url;
    } catch (err) {
      setBillingError(err?.message || "Could not start checkout");
      setCheckoutLoading(false);
    }
  };

  if (!phase || !isPhaseUnlocked(phase.id)) {
    return <Navigate to="/journey-phases" replace />;
  }

  const currentQuestion = questions[currentIdx];
  const billingSource = billing || getStoredBillingUser();
  const journeyQuestionNumber = getJourneyQuestionNumber(phaseId, currentIdx);
  const isPhaseOneOrbJourney = Number(phaseId) === 1;
  const isCurrentQuestionLocked = currentQuestion && !isPhaseOneOrbJourney && !isJourneyQuestionUnlocked(journeyQuestionNumber, billingSource);
  const questionLabel = currentQuestion
    ? `Q.${currentIdx + 1}. ${currentQuestion.text}`
    : "";

  const sidebarLabels =
    Number(phaseId) === 1 ? PHASE_1_MANIFESTO_STEPS : questions.map((q) => q.shortLabel);
  const totalQuestions = questions.length || sidebarLabels.length;
  const phaseNumber = Number(phaseId) || 1;
  const totalPhases = JOURNEY_PHASES.length;
  const completedPhases = Math.max(0, Math.min(totalPhases, phaseNumber - 1));
  const phaseQuestionProgress = totalQuestions > 0 ? (currentIdx + 1) / totalQuestions : 0;
  const phaseStatus = {
    title: `Phase ${phaseNumber} in progress`,
    subtitle: `${completedPhases} phase${completedPhases === 1 ? "" : "s"} complete · ${phase?.title || "Brand discovery"}`,
    progress: Math.round(((completedPhases + phaseQuestionProgress) / totalPhases) * 100),
  };
  const activeNudge = nudges.length > 0 ? nudges[nudgeIndex % nudges.length] : "";
  const progressPercent =
    totalQuestions > 0
      ? Math.round(((currentIdx + 1) / totalQuestions) * 100)
      : 0;
  const answeredInPhaseCount = questions.filter((q) => String(answers[q.key] ?? "").trim()).length;
  const levelXpPercent = totalQuestions > 0 ? Math.round((answeredInPhaseCount / totalQuestions) * 100) : 0;
  const streakCount = Math.max(0, answeredInPhaseCount);
  const remainingQuestions = Math.max(0, totalQuestions - answeredInPhaseCount);
  const isBossQuestion = totalQuestions > 0 && currentIdx === totalQuestions - 1;
  const missionLabel = isBossQuestion
    ? "Boss Question"
    : `Mission ${Math.min(currentIdx + 1, totalQuestions)}/${totalQuestions}`;
  const missionHint = allPhaseAnswered
    ? `Level ${phaseNumber} is ready to clear.`
    : remainingQuestions === 1
      ? "1 answer away from Level Clear."
      : `${remainingQuestions} answers away from Level Clear.`;
  const submitLabel = submitting
    ? orbChecking
      ? "ORB checking…"
      : "Saving…"
    : isFinalPhase && allPhaseAnswered
      ? "Save to Finish"
      : allPhaseAnswered
        ? `Complete Level ${phaseNumber}`
        : "Submit";

  // Committed verdict (after Send) takes priority; otherwise show the live preview.
  const isLiveVerdict = !orbChecking && !orbVerdict && (livePreviewChecking || !!livePreview);
  const viewVerdict = orbVerdict || livePreview;
  const viewChecking = orbChecking || (isLiveVerdict && livePreviewChecking && !livePreview);
  const showVerdictPanel = orbChecking || orbVerdict || livePreviewChecking || !!livePreview;
  const apiResponsePayload = viewVerdict
    ? viewVerdict.view_api_response || {
        event: "orb.view_api_response",
        data: {
          metadata: viewVerdict.metadata || null,
          crux_context: viewVerdict.crux_context || null,
          confidence_tracking: viewVerdict.confidence_tracking || null,
        },
      }
    : null;

  return (
    <div className="pq-page">
      <SessionTitleModal
        open={showTitleModal}
        title={modalTitle}
        onTitleChange={setModalTitle}
        agencies={agencies}
        selectedAgency={selectedAgency}
        onAgencyChange={setSelectedAgency}
        agenciesLoading={agenciesLoading}
        agenciesError={agenciesError}
        showAgencyPicker={!isAgencyUser}
        onSubmit={handleCreateSession}
        loading={modalLoading}
        error={modalError}
      />

      <ChatNavbar
        sessionId={sessionId}
        onSave={handleSubmitClick}
        showSaveButton
        saveButtonLabel={submitLabel}
        saveButtonSavingLabel={submitLabel}
        saveDisabled={submitting || !allPhaseAnswered}
        saveButtonDisabledTitle={`Answer all ${totalQuestions} questions to submit`}
        saveButtonTitle={
          isFinalPhase && allPhaseAnswered
            ? "Hit save button"
            : allPhaseAnswered
              ? `Complete Level ${phaseNumber}`
              : undefined
        }
        showDownloadButton={false}
        showLogoutButton
        phaseStatus={phaseStatus}
        leadingAction={
          <button
            type="button"
            className="pq-navbar-menu-btn"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? "Close question menu" : "Open question menu"}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        }
      />

      <div className="pq-body">
        <aside className={`pq-sidebar${sidebarOpen ? " open" : ""}`} aria-hidden={showTitleModal}>
          <h2 className="pq-sidebar-title">Brand Manifesto</h2>
          <div className="pq-sidebar-divider" />
          <nav className="pq-sidebar-nav">
            {(questions.length ? questions : sidebarLabels.map((l, i) => ({ shortLabel: l, id: i }))).map(
              (item, i) => {
                const label = item.shortLabel || sidebarLabels[i] || `Step ${i + 1}`;
                const isActive = i === currentIdx;
                const isAnswered = item.key && answers[item.key]?.trim();
                const isBossStep = i === totalQuestions - 1;
                return (
                  <button
                    key={item.id ?? i}
                    type="button"
                    className={`pq-sidebar-item ${isActive ? "active" : ""} ${isAnswered ? "answered" : ""} ${isBossStep ? "boss" : ""}`}
                    onClick={() => {
                      setCurrentIdx(i);
                      setSidebarOpen(false);
                    }}
                    disabled={i >= questions.length && questions.length > 0}
                  >
                    <span className="pq-sidebar-num">{String(i + 1).padStart(2, "0")}</span>
                    <span className="pq-sidebar-label">{label}</span>
                  </button>
                );
              },
            )}
          </nav>
        </aside>
        <button
          type="button"
          className={`pq-sidebar-backdrop${sidebarOpen ? " open" : ""}`}
          aria-label="Close question menu"
          onClick={() => setSidebarOpen(false)}
        />

        <main className="pq-main" aria-hidden={showTitleModal}>
          {loading ? (
            <p className="pq-status">Loading questions…</p>
          ) : loadError ? (
            <p className="pq-status pq-status--error">{loadError}</p>
          ) : questions.length === 0 || !currentQuestion ? (
            <p className="pq-status">No questions available.</p>
          ) : isCurrentQuestionLocked ? (
            <div className="pq-paywall" aria-live="polite">
              <p className="pq-paywall-kicker">Subscription required</p>
              <h2>Continue after question {journeyQuestionNumber - 1}</h2>
              {billingLoading ? (
                <p>Checking your subscription…</p>
              ) : billing?.plan ? (
                <p>
                  Unlock the remaining questions with {billing.plan.name} · {billing.plan.price_display}
                </p>
              ) : (
                <p>Ask admin to add an active subscription plan.</p>
              )}
              {billingError && <p className="pq-paywall-error">{billingError}</p>}
              <button
                type="button"
                className="pq-paywall-button"
                onClick={handleQuestionUpgrade}
                disabled={billingLoading || checkoutLoading || !billing?.plan}
              >
                {checkoutLoading ? "Opening checkout…" : "Upgrade & Continue"}
              </button>
            </div>
          ) : (
            <>
              <section className="pq-game-hud" aria-label="Journey level progress">
                <div className="pq-level-chip">
                  <span>Level {phaseNumber}</span>
                  <strong>{phase?.title || "Brand discovery"}</strong>
                </div>
                <div className={`pq-mission-chip${isBossQuestion ? " pq-mission-chip--boss" : ""}`}>
                  <span>{missionLabel}</span>
                  <strong>{missionHint}</strong>
                </div>
                <div className="pq-xp-meter" aria-hidden="true">
                  <div className="pq-xp-meter-top">
                    <span>XP</span>
                    <strong>{levelXpPercent}%</strong>
                  </div>
                  <div className="pq-xp-track">
                    <span style={{ width: `${levelXpPercent}%` }} />
                  </div>
                </div>
                <div className="pq-streak-chip">
                  <span>{streakCount}</span>
                  Answer streak
                </div>
              </section>

              {answerReward && (
                <div className="pq-answer-reward" key={answerReward.id} aria-live="polite">
                  <span className="pq-answer-reward-orb" aria-hidden="true" />
                  <div>
                    <strong>{answerReward.title}</strong>
                    <p>{answerReward.text}</p>
                    <small>Streak x{answerReward.streak}</small>
                  </div>
                  <span className="pq-reward-bubble pq-reward-bubble--1" aria-hidden="true" />
                  <span className="pq-reward-bubble pq-reward-bubble--2" aria-hidden="true" />
                  <span className="pq-reward-bubble pq-reward-bubble--3" aria-hidden="true" />
                </div>
              )}

              <div className="pq-progress-wrap">
                <div className="pq-progress-track">
                  <div className="pq-progress-fill" style={{ width: `${progressPercent}%` }} />
                </div>
                <p className="pq-progress-label">
                  Question {currentIdx + 1} of {totalQuestions}
                </p>
              </div>

              <div className="pq-orb-row">
                {replyVisible && viewVerdict?.follow_up_question && (
                  <div className="pq-followup-wrap" aria-live="polite">
                    <div className="pq-followup-bubble pq-followup-bubble--enter">
                      <span className="pq-followup-badge">Brand Godfather asks</span>
                      <p>{viewVerdict.follow_up_question}</p>
                    </div>
                  </div>
                )}
                <OrbPresence className="pq-orb-presence">
                  <BrandOrb size="welcome" />
                </OrbPresence>
                <div className="pq-nudges-wrap" aria-live="polite">
                  <span className="pq-nudges-badge"></span>
                  {nudgesLoading && (
                    <p className="pq-nudges-status">Thinking of ideas…</p>
                  )}
                  {!nudgesLoading && nudgeQuality && !replyVisible && (
                    <div className={`pq-nudges-panel${nudgesFading ? " pq-nudges-panel--dissolve" : ""}`}>
                      {nudgeQuality.reason && (
                        <p className="pq-nudges-reason">{nudgeQuality.reason}</p>
                      )}
                      {/* Hidden per request: rewritten-answer quote bubble (echoed user answer) */}
                      {/* {nudgeQuote?.quote && (
                        <blockquote className="pq-nudge-quote">
                          {nudgeQuote.quote}
                        </blockquote>
                      )} */}
                      {activeNudge && (
                        <>
                          {/* Hidden per request: intermediate "Let's make it sharper" lead text */}
                          {/* <p className="pq-nudges-lead">
                            {nudgeQuality.quality === "strong"
                              ? "Make it even sharper:"
                              : "Let’s make it stronger like this:"}
                          </p> */}
                          <button
                            type="button"
                            className="pq-nudge-chip"
                            onClick={() => applyNudge(activeNudge)}
                          >
                            {activeNudge}
                          </button>
                          {nudges.length > 1 && (
                            <p className="pq-nudges-status pq-nudges-status--muted">
                              Tap Help me to go deeper for next suggestion ({nudgeIndex + 1}/{nudges.length})
                            </p>
                          )}
                        </>
                      )}
                    </div>
                  )}
                  {!nudgesLoading &&
                    !activeNudge &&
                    inputValue.trim().length >= 3 && (
                      <p className="pq-nudges-status pq-nudges-status--muted">
                        ORB will evaluate this answer when you submit it.
                      </p>
                    )}
                  {replyVisible && viewVerdict?.reply && (
                    <div className="pq-orb-reply pq-orb-reply--enter" aria-live="polite">
                      <span className="pq-orb-reply-badge">Brand Godfather says</span>
                      <p>{viewVerdict.reply}</p>
                    </div>
                  )}
                  {SHOW_LEGACY_ORB_INTELLIGENCE_PANEL && showVerdictPanel && showApiData && (
                    <div
                      className={`pq-orb-verdict pq-orb-verdict--${String(
                        viewVerdict?.status || "checking",
                      ).toLowerCase()}${isLiveVerdict ? " pq-orb-verdict--live" : ""}`}
                    >
                      <div className="pq-orb-verdict-head">
                        <span>ORB Intelligence{isLiveVerdict ? " · LIVE" : ""}</span>
                        <strong>{viewChecking ? "CHECKING" : viewVerdict.status}</strong>
                      </div>
                      {!viewChecking && viewVerdict?.interruption_type === "vendor_language" && (
                        <div className="pq-vendor-block" role="alert">
                          <span>Vendor trap caught</span>
                          {viewVerdict.blocked_phrases?.length > 0 && (
                            <strong>{viewVerdict.blocked_phrases.join(", ")}</strong>
                          )}
                          <p>Others can be vendors. This brand cannot. Replace service talk with what you stand for, who you are here for, and why they should care.</p>
                        </div>
                      )}
                      {!viewChecking && viewVerdict?.interruption_type === "contradiction" && (
                        <div className="pq-contradiction-block" role="alert">
                          <span>Contradiction caught</span>
                          {viewVerdict.contradiction_result?.conflicting_q_id && (
                            <strong>Conflicts with {viewVerdict.contradiction_result.conflicting_q_id}</strong>
                          )}
                          <p>{viewVerdict.contradiction_message || "This answer conflicts with an earlier answer. Resolve the truth before moving on."}</p>
                        </div>
                      )}
                      {!viewChecking && viewVerdict?.interruption_type === "adaptive_coaching" && (
                        <div className="pq-adaptive-block" role="alert">
                          <span>Adaptive challenge raised</span>
                          <strong>Pressure {viewVerdict.pressure_used || "n/a"} · Resistance {viewVerdict.resistance_count || 0}</strong>
                          <p>The ORB is increasing intensity because this answer is still avoiding the deeper brand truth.</p>
                        </div>
                      )}
                      {!viewChecking && viewVerdict?.breakthrough_detected && (
                        <div className="pq-breakthrough-block" role="status">
                          <span>Breakthrough recognized</span>
                          <strong>{viewVerdict.breakthrough_seed || "Brand seed captured"}</strong>
                          <p>{viewVerdict.breakthrough_reason || "That is the truth/edge. The ORB captured it as a brand seed."}</p>
                        </div>
                      )}
                      <div className="pq-orb-verdict-grid">
                        <span>status</span>
                        <strong>{viewChecking ? "CHECKING" : viewVerdict.status}</strong>
                        <span>discovery_id</span>
                        <strong>{viewChecking ? "..." : viewVerdict.associated_discovery_id || "none"}</strong>
                        <span>target_confidence_threshold</span>
                        <strong>{viewChecking ? "..." : viewVerdict.target_confidence_threshold ?? "n/a"}</strong>
                        <span>canonical_question</span>
                        <strong>{viewChecking ? "..." : viewVerdict.metadata?.canonical_question || "none"}</strong>
                        <span>challenge_type</span>
                        <strong>{viewChecking ? "..." : viewVerdict.challenge_type || "none"}</strong>
                        <span>pressure_used</span>
                        <strong>{viewChecking ? "..." : viewVerdict.pressure_used ?? "n/a"}</strong>
                        <span>resistance_count</span>
                        <strong>{viewChecking ? "..." : viewVerdict.resistance_count ?? 0}</strong>
                        <span>emotional_state</span>
                        <strong>{viewChecking ? "..." : viewVerdict.emotional_state || "neutral"}</strong>
                        <span>tone_mode</span>
                        <strong>{viewChecking ? "..." : viewVerdict.tone_mode || "direct_challenge"}</strong>
                        <span>next_q_id</span>
                        <strong>{viewChecking ? "..." : viewVerdict.next_q_id}</strong>
                        <span>depth_score</span>
                        <strong>{viewChecking ? "..." : viewVerdict.depth_score}</strong>
                        <span>breakthrough</span>
                        <strong>{viewChecking ? "..." : viewVerdict.breakthrough_detected ? `yes · ${viewVerdict.breakthrough_score}` : "no"}</strong>
                        <span>breakthrough_seed</span>
                        <strong>{viewChecking ? "..." : viewVerdict.breakthrough_seed || "none"}</strong>
                        <span>reply</span>
                        <strong>{viewChecking ? "..." : viewVerdict.reply}</strong>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="pq-chat">
                <div className="pq-bubble pq-bubble--bot">
                  <img src="/Group%2021.svg" alt="" className="pq-bot-avatar" />
                  <div className="pq-bubble-text">
                    {isBossQuestion && <span className="pq-boss-label">Boss Question</span>}
                    {questionLabel}
                  </div>
                </div>
              </div>

              <div className="pq-input-wrap">
                <div
                  className={`pq-input-row${
                    inputValue.includes("\n") || inputValue.length > 72
                      ? " pq-input-row--multiline"
                      : ""
                  }`}
                >
                  <textarea
                    ref={inputRef}
                    rows={1}
                    className="pq-input"
                    value={inputValue}
                    onChange={(e) => {
                      currentInputAiDraftRef.current = false;
                      setInputValue(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        if (allPhaseAnswered) {
                          if (isFinalPhase) {
                            toast.info("Hit save button");
                          } else {
                            handlePhaseSubmit();
                          }
                        } else {
                          handleSend();
                        }
                      }
                    }}
                    placeholder={currentQuestion.placeholder}
                    aria-label="Your answer"
                  />
                  <div className="pq-refine-wrap">
                    <div className="pq-refine-tip">
                      Help me to go deeper
                    </div>
                    <button
                      type="button"
                      className="pq-icon-btn"
                      title="Help me to go deeper"
                      aria-label="Help me to go deeper"
                      onClick={handleRefineClick}
                      disabled={LEGACY_RAG_V2_DISABLED || nudgesLoading || inputValue.trim().length < 3}
                    >
                      <img src={chatIcon1} alt="" />
                    </button>
                  </div>
                  <button
                    type="button"
                    className={`pq-icon-btn pq-icon-btn--send${allPhaseAnswered ? " pq-icon-btn--send-locked" : ""}`}
                    onClick={handleSendClick}
                    disabled={submitting}
                    title={allPhaseAnswered ? "Hit submit button" : "Send"}
                    aria-label="Send"
                  >
                    <img src={chatIcon2} alt="" />
                  </button>
                </div>

                {showVerdictPanel && (
                  <button
                    type="button"
                    className="pq-api-data-link pq-api-data-link--under-input"
                    onClick={() => {
                      if (!showApiData) persistViewApiResponsePayload(apiResponsePayload);
                      setShowApiData((v) => !v);
                    }}
                  >
                    {showApiData ? "Hide API response" : "View API response"}
                    {viewChecking ? " (checking...)" : ""}
                  </button>
                )}

                {showVerdictPanel && showApiData && apiResponsePayload && (
                  <pre className="pq-api-response-json">
                    {JSON.stringify(apiResponsePayload, null, 2)}
                  </pre>
                )}

                {SHOW_BGF_HELP_PANEL && (
                  <div className="pq-bgf-help" aria-live="polite">
                    <div className="pq-bgf-help-head">
                      <span>Ask the Brand Godfather</span>
                      {bgfHelpLoading && <small>Thinking...</small>}
                    </div>
                    <div className="pq-bgf-help-actions">
                      {BGF_HELP_ACTIONS.map((action) => (
                        <button
                          key={action.intent}
                          type="button"
                          className="pq-bgf-help-chip"
                          onClick={() => handleBgfHelp(action.intent)}
                          disabled={bgfHelpLoading || !sessionId || !currentQuestion?.id}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                    <form
                      className="pq-bgf-ask-form"
                      onSubmit={(event) => {
                        event.preventDefault();
                        handleBgfHelp("ask", bgfAskText);
                      }}
                    >
                      <input
                        type="text"
                        value={bgfAskText}
                        onChange={(event) => setBgfAskText(event.target.value)}
                        placeholder="Ask anything about this question..."
                        disabled={bgfHelpLoading}
                      />
                      <button type="submit" disabled={bgfHelpLoading || !bgfAskText.trim()}>
                        Ask
                      </button>
                    </form>
                    {bgfHelpResponse?.answer && (
                      <div className="pq-bgf-help-response">
                        <strong>{bgfHelpResponse.title || "Brand Godfather"}</strong>
                        <p>{bgfHelpResponse.answer}</p>
                        {bgfHelpResponse.example_answer && (
                          <button
                            type="button"
                            className="pq-bgf-example"
                            onClick={() => applyNudge(bgfHelpResponse.example_answer)}
                          >
                            {bgfHelpResponse.example_answer}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/*
                <div className="pq-footer-row">
                  <button
                    type="button"
                    className={`pq-submit-btn${isFinalPhase && allPhaseAnswered ? " pq-submit-btn--locked" : ""}`}
                    onClick={handleSubmitClick}
                    disabled={submitting || !allPhaseAnswered}
                    title={
                      isFinalPhase && allPhaseAnswered
                        ? "Hit save button"
                        : allPhaseAnswered
                        ? `Complete Level ${phaseNumber}`
                        : `Answer all ${totalQuestions} questions to submit`
                    }
                  >
                    {submitLabel}
                  </button>
                </div>
                */}
              </div>

              <button
                type="button"
                className="pq-arrow-btn pq-arrow-btn--left-floating"
                onClick={handlePrev}
                disabled={currentIdx === 0}
                aria-label="Previous question"
              >
                ←
              </button>
              <button
                type="button"
                className="pq-arrow-btn pq-arrow-btn--right-floating"
                onClick={handleNextNav}
                disabled={currentIdx >= questions.length - 1}
                aria-label="Next question"
              >
                →
              </button>

              {submitError && <p className="pq-submit-error">{submitError}</p>}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
