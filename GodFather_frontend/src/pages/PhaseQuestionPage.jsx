import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useNavigate, useParams, Navigate } from "react-router-dom";
import { toast } from "react-toastify";
import ChatNavbar from "./ChatNavbar";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import authService from "../services/authService";
import {
  getJourneyPhase,
  isPhaseUnlocked,
  unlockPhaseAfterComplete,
  PHASE_1_MANIFESTO_STEPS,
  TOTAL_JOURNEY_QUESTIONS,
  countStoredJourneyAnswers,
  getPhaseAnswersStorageKey,
} from "../constants/journeyPhases";
import chatIcon1 from "../assets/chat-icon1.png";
import chatIcon2 from "../assets/chat-icon2.png";
import {
  extractApplicableNudgeText,
  scoreAnswerQualityLocal,
} from "../utils/answerQuality";
import "./PhaseQuestionPage.css";

function SessionTitleModal({
  open,
  title,
  onTitleChange,
  agencies,
  selectedAgency,
  onAgencyChange,
  agenciesLoading,
  agenciesError,
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
  const [nudgeIndex, setNudgeIndex] = useState(0);
  const [nudgesLoading, setNudgesLoading] = useState(false);
  const [journeyAnsweredCount, setJourneyAnsweredCount] = useState(0);
  const nudgesDebounceRef = useRef(null);
  const nudgePickedRef = useRef(false);

  const storageKey = getPhaseAnswersStorageKey(sessionId, phaseId);

  useEffect(() => {
    if (session) setShowTitleModal(false);
  }, [session]);

  useEffect(() => {
    if (!showTitleModal) return;
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
  }, [showTitleModal]);

  useEffect(() => {
    if (initialSession || session) return;
    let cancelled = false;
    (async () => {
      try {
        const list = await authService.getSessions();
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
        const res = await authService.getQuestions();
        if (cancelled) return;
        let all = Array.isArray(res) ? res : res?.questions || [];
        // Backend questions are stored by `Question.stage`.
        // Frontend phaseId maps to stage numbers:
        // phase 1 -> stage 1 (Basic), phase 2 -> stage 2 (Foundation), phase 3 -> stage 3 (Identity)
        const targetStage = Number(phaseId) || 1;
        all = all
          .filter((q) => String(q.stage) === String(targetStage))
          .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

        const mapped = all.map((q, i) => ({
          id: q.id,
          key: `q_${q.id}`,
          text: q.text || q.title || `Question ${i + 1}`,
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

        setAnswers((prev) => {
          const next = { ...prev };
          (Array.isArray(remoteAnswers) ? remoteAnswers : []).forEach((a) => {
            const key = idToKey[String(a.question)] || `q_${a.question}`;
            if (typeof a.answer_text === "string" && a.answer_text.trim() !== "") {
              next[key] = a.answer_text;
            }
          });
          localStorage.setItem(storageKey, JSON.stringify(next));
          return next;
        });
      } catch {
        /* keep local cache */
      }
    }

    loadExistingAnswers();
    return () => {
      cancelled = true;
    };
  }, [sessionId, questions, storageKey]);

  const refreshJourneyAnswerCount = async () => {
    if (!sessionId) {
      const localCount = countStoredJourneyAnswers(null);
      setJourneyAnsweredCount(localCount);
      return localCount;
    }
    try {
      const remoteAnswers = await authService.getAnswers(sessionId, {});
      const count = (Array.isArray(remoteAnswers) ? remoteAnswers : []).filter((a) =>
        String(a.answer_text ?? "").trim(),
      ).length;
      setJourneyAnsweredCount(count);
      return count;
    } catch {
      const localCount = countStoredJourneyAnswers(sessionId);
      setJourneyAnsweredCount(localCount);
      return localCount;
    }
  };

  useEffect(() => {
    refreshJourneyAnswerCount();
  }, [sessionId, answers]);

  useEffect(() => {
    const q = questions[currentIdx];
    if (!q) return;
    const saved = answers[q.key];
    setInputValue(saved != null ? String(saved) : "");
    setNudges([]);
    setNudgeQuality(null);
    setNudgeIndex(0);
    setNudgesLoading(false);
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.focus();
    }
  }, [currentIdx, questions, answers]);

  useLayoutEffect(() => {
    resizeInput();
  }, [inputValue, currentIdx]);

  const fetchNudges = async (hint, question) => {
    const q = question || questions[currentIdx];
    if (!q) return;

    setNudgesLoading(true);
    setNudgeQuality(scoreAnswerQualityLocal(q, hint));

    try {
      const res = await authService.getAiAnswerSuggestions(sessionId, q.id, hint);
      let list = [];
      if (Array.isArray(res)) {
        list = res;
      } else if (res && typeof res === "object") {
        list = res.suggestions ?? res.suggestion ?? [];
        if (res.quality && res.quality_label) {
          setNudgeQuality({
            quality: res.quality,
            quality_label: res.quality_label,
            reason: res.reason || "",
          });
        }
      }
      const cleaned = (Array.isArray(list) ? list : [])
        .map((s) => extractApplicableNudgeText(String(s).trim()))
        .filter(Boolean);
      setNudges(cleaned);
      setNudgeIndex(0);
    } catch {
      setNudges([]);
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
    const cleaned = extractApplicableNudgeText(text);
    setInputValue(cleaned);
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

  const persistAnswers = (next) => {
    setAnswers(next);
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      /* ignore */
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
      const agencyNum = Number(selectedAgency) || 0;
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
    } catch (err) {
      setModalError(err?.message || "Failed to create session");
    } finally {
      setModalLoading(false);
    }
  };

  const allPhaseAnswered =
    questions.length > 0 &&
    questions.every((q) => String(answers[q.key] ?? "").trim());

  const allJourneyAnswered = journeyAnsweredCount >= TOTAL_JOURNEY_QUESTIONS;
  const isFinalPhase = Number(phaseId) === 3;

  const saveCurrentAnswer = async () => {
    const currentQuestion = questions[currentIdx];
    if (!currentQuestion) return null;
    const value = inputValue.trim();
    if (!value) {
      setSubmitError("Please answer before submitting.");
      return null;
    }
    setSubmitError("");

    const nextAnswers = { ...answers, [currentQuestion.key]: value };
    persistAnswers(nextAnswers);

    const sid = sessionId;
    const apiQuestionId = currentQuestion.raw?.id ?? currentQuestion.id;

    if (sid && apiQuestionId) {
      await authService.createAnswer(sid, {
        question: Number(apiQuestionId),
        answer_text: value,
      });
    }
    await refreshJourneyAnswerCount();
    return nextAnswers;
  };

  const handleSend = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const nextAnswers = await saveCurrentAnswer();
      if (!nextAnswers) return;

      const phaseComplete =
        questions.length > 0 &&
        questions.every((q) => String(nextAnswers[q.key] ?? "").trim());

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

      unlockPhaseAfterComplete(phaseId);
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

  const handleSave = async () => {
    const q = questions[currentIdx];
    if (!q) return;
    const value = inputValue.trim();
    let nextAnswers = { ...answers };
    if (value) {
      nextAnswers = { ...answers, [q.key]: value };
      persistAnswers(nextAnswers);
      const sid = sessionId;
      const apiQuestionId = q.raw?.id ?? q.id;
      if (sid && apiQuestionId) {
        try {
          await authService.createAnswer(sid, {
            question: Number(apiQuestionId),
            answer_text: value,
          });
        } catch {
          /* non-fatal for local save */
        }
      }
    }

    const answeredInPhase =
      questions.length > 0 &&
      questions.every((item) => String(nextAnswers[item.key] ?? "").trim());
    const refreshedCount = await refreshJourneyAnswerCount();
    const journeyDone = (refreshedCount ?? journeyAnsweredCount) >= TOTAL_JOURNEY_QUESTIONS;

    if (isFinalPhase && answeredInPhase && journeyDone) {
      navigate(`/phase-complete/${phaseId}`);
      return;
    }
    toast.success("Saved");
  };

  const handleSubmitClick = () => {
    if (isFinalPhase && allPhaseAnswered) {
      toast.info("Hit save button");
      return;
    }
    handlePhaseSubmit();
  };

  if (!phase || !isPhaseUnlocked(phase.id)) {
    return <Navigate to="/journey-phases" replace />;
  }

  const currentQuestion = questions[currentIdx];
  const questionLabel = currentQuestion
    ? `Q.${currentIdx + 1}. ${currentQuestion.text}`
    : "";

  const sidebarLabels =
    Number(phaseId) === 1 ? PHASE_1_MANIFESTO_STEPS : questions.map((q) => q.shortLabel);
  const totalQuestions = questions.length || sidebarLabels.length;
  const activeNudge = nudges.length > 0 ? nudges[nudgeIndex % nudges.length] : "";
  const progressPercent =
    totalQuestions > 0
      ? Math.round(((currentIdx + 1) / totalQuestions) * 100)
      : 0;

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
        onSubmit={handleCreateSession}
        loading={modalLoading}
        error={modalError}
      />

      <ChatNavbar
        sessionId={sessionId}
        onSave={handleSave}
        showSaveButton
        saveDisabled={!allJourneyAnswered}
        showDownloadButton={false}
        showLogoutButton
      />

      <div className="pq-body">
        <aside className="pq-sidebar" aria-hidden={showTitleModal}>
          <h2 className="pq-sidebar-title">Brand Manifesto</h2>
          <div className="pq-sidebar-divider" />
          <nav className="pq-sidebar-nav">
            {(questions.length ? questions : sidebarLabels.map((l, i) => ({ shortLabel: l, id: i }))).map(
              (item, i) => {
                const label = item.shortLabel || sidebarLabels[i] || `Step ${i + 1}`;
                const isActive = i === currentIdx;
                const isAnswered = item.key && answers[item.key]?.trim();
                return (
                  <button
                    key={item.id ?? i}
                    type="button"
                    className={`pq-sidebar-item ${isActive ? "active" : ""} ${isAnswered ? "answered" : ""}`}
                    onClick={() => setCurrentIdx(i)}
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

        <main className="pq-main" aria-hidden={showTitleModal}>
          {loading ? (
            <p className="pq-status">Loading questions…</p>
          ) : loadError ? (
            <p className="pq-status pq-status--error">{loadError}</p>
          ) : questions.length === 0 || !currentQuestion ? (
            <p className="pq-status">No questions available.</p>
          ) : (
            <>
              <div className="pq-progress-wrap">
                <div className="pq-progress-track">
                  <div className="pq-progress-fill" style={{ width: `${progressPercent}%` }} />
                </div>
                <p className="pq-progress-label">
                  Question {currentIdx + 1} of {totalQuestions}
                </p>
              </div>

              <div className="pq-orb-row">
                <OrbPresence className="pq-orb-presence">
                  <BrandOrb size="welcome" />
                </OrbPresence>
                <div className="pq-nudges-wrap" aria-live="polite">
                  <span className="pq-nudges-badge">Nudges, Recommendations</span>
                  {nudgesLoading && (
                    <p className="pq-nudges-status">Thinking of ideas…</p>
                  )}
                  {!nudgesLoading && nudgeQuality && (
                    <div className="pq-nudges-panel">
                      <p
                        className={`pq-nudge-quality pq-nudge-quality--${nudgeQuality.quality || "too_weak"}`}
                      >
                        {nudgeQuality.quality_label}
                      </p>
                      {nudgeQuality.reason && (
                        <p className="pq-nudges-reason">{nudgeQuality.reason}</p>
                      )}
                      {activeNudge && (
                        <>
                          <p className="pq-nudges-lead">
                            {nudgeQuality.quality === "strong"
                              ? "Make it even sharper:"
                              : "Try this instead:"}
                          </p>
                          <button
                            type="button"
                            className="pq-nudge-chip"
                            onClick={() => applyNudge(activeNudge)}
                          >
                            {activeNudge}
                          </button>
                          {nudges.length > 1 && (
                            <p className="pq-nudges-status pq-nudges-status--muted">
                              Tap AI Refine for next suggestion ({nudgeIndex + 1}/{nudges.length})
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
                        Keep typing — we&apos;ll suggest stronger replies.
                      </p>
                    )}
                </div>
              </div>

              <div className="pq-chat">
                <div className="pq-bubble pq-bubble--bot">
                  <img src="/Group%2021.svg" alt="" className="pq-bot-avatar" />
                  <div className="pq-bubble-text">{questionLabel}</div>
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
                    onChange={(e) => setInputValue(e.target.value)}
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
                      Sharpen it the World-Famous way. Let Godfather refine this.
                    </div>
                    <button
                      type="button"
                      className="pq-icon-btn"
                      title="AI refine"
                      aria-label="AI refine"
                      onClick={handleRefineClick}
                      disabled={nudgesLoading || inputValue.trim().length < 3}
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

                <div className="pq-footer-row">
                  <div className="pq-nav-arrows">
                    <button
                      type="button"
                      className="pq-arrow-btn"
                      onClick={handlePrev}
                      disabled={currentIdx === 0}
                      aria-label="Previous question"
                    >
                      ←
                    </button>
                    <button
                      type="button"
                      className="pq-arrow-btn"
                      onClick={handleNextNav}
                      disabled={currentIdx >= questions.length - 1}
                      aria-label="Next question"
                    >
                      →
                    </button>
                  </div>
                  <button
                    type="button"
                    className={`pq-submit-btn${isFinalPhase && allPhaseAnswered ? " pq-submit-btn--locked" : ""}`}
                    onClick={handleSubmitClick}
                    disabled={submitting || !allPhaseAnswered}
                    title={
                      isFinalPhase && allPhaseAnswered
                        ? "Hit save button"
                        : allPhaseAnswered
                        ? "Submit this phase"
                        : `Answer all ${totalQuestions} questions to submit`
                    }
                  >
                    {submitting ? "Saving…" : "Submit"}
                  </button>
                </div>
              </div>

              {submitError && <p className="pq-submit-error">{submitError}</p>}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
