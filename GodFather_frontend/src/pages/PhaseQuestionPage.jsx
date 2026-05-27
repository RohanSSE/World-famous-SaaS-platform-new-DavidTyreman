import { useEffect, useRef, useState } from "react";
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
} from "../constants/journeyPhases";
import chatQuestionIcon from "../assets/ChatQuestionIcon.png";
import chatIcon1 from "../assets/chat-icon1.png";
import chatIcon2 from "../assets/chat-icon2.png";
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
  const [nudgeIndex, setNudgeIndex] = useState(0);
  const [nudgesLoading, setNudgesLoading] = useState(false);
  const nudgesDebounceRef = useRef(null);
  const nudgePickedRef = useRef(false);

  const storageKey = sessionId ? `phaseAnswers_${sessionId}_p${phaseId}` : `phaseAnswers_p${phaseId}`;

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
  }, [sessionId]);

  useEffect(() => {
    const q = questions[currentIdx];
    if (!q) return;
    const saved = answers[q.key];
    setInputValue(saved != null ? String(saved) : "");
    setNudges([]);
    setNudgeIndex(0);
    setNudgesLoading(false);
    if (inputRef.current) inputRef.current.focus();
  }, [currentIdx, questions, answers]);

  const fetchNudges = async (hint, questionId) => {
    setNudgesLoading(true);
    try {
      const res = await authService.getAiAnswerSuggestions(sessionId, questionId, hint);
      let list = [];
      if (Array.isArray(res)) {
        list = res;
      } else if (res && typeof res === "object") {
        list = res.suggestions ?? res.suggestion ?? [];
      }
      const cleaned = (Array.isArray(list) ? list : [])
        .map((s) => String(s).trim())
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
      setNudgesLoading(false);
      return;
    }

    nudgesDebounceRef.current = setTimeout(async () => {
      if (nudgePickedRef.current) {
        nudgePickedRef.current = false;
        return;
      }
      await fetchNudges(hint, q.id);
    }, 500);

    return () => {
      if (nudgesDebounceRef.current) clearTimeout(nudgesDebounceRef.current);
    };
  }, [inputValue, currentIdx, questions, sessionId]);

  const applyNudge = (text) => {
    nudgePickedRef.current = true;
    setInputValue(text);
    setNudgeIndex(0);
    inputRef.current?.focus();
  };

  const handleRefineClick = async () => {
    const q = questions[currentIdx];
    const hint = inputValue.trim();
    if (!sessionId || !q?.id || hint.length < 3) return;

    if (nudges.length > 1) {
      setNudgeIndex((prev) => (prev + 1) % nudges.length);
      return;
    }
    await fetchNudges(hint, q.id);
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

  const handleSubmit = async () => {
    const currentQuestion = questions[currentIdx];
    if (!currentQuestion) return;
    const value = inputValue.trim();
    if (!value) {
      setSubmitError("Please answer before submitting.");
      return;
    }
    setSubmitError("");
    setSubmitting(true);

    const nextAnswers = { ...answers, [currentQuestion.key]: value };
    persistAnswers(nextAnswers);

    const sid = sessionId;
    const apiQuestionId = currentQuestion.raw?.id ?? currentQuestion.id;

    if (sid && apiQuestionId) {
      try {
        await authService.createAnswer(sid, {
          question: Number(apiQuestionId),
          answer_text: value,
        });
      } catch (err) {
        setSubmitError(err?.message || "Failed to save answer");
        setSubmitting(false);
        return;
      }
    }

    setSubmitting(false);

    if (currentIdx < questions.length - 1) {
      setCurrentIdx((i) => i + 1);
      return;
    }

    unlockPhaseAfterComplete(phaseId);
    const completedPhase = getJourneyPhase(phaseId);
    if (completedPhase?.complete) {
      navigate(`/phase-complete/${phaseId}`);
      return;
    }
    navigate("/ChatKickoffPage");
  };

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx((i) => i - 1);
  };

  const handleNextNav = () => {
    if (currentIdx < questions.length - 1) setCurrentIdx((i) => i + 1);
  };

  const handleSave = () => {
    const q = questions[currentIdx];
    if (!q) return;
    persistAnswers({ ...answers, [q.key]: inputValue });
    toast.success("Saved");
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
                  {!nudgesLoading && !!activeNudge && (
                    <div className="pq-nudges-panel">
                      <p className="pq-nudges-lead">You could also say:</p>
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
                  <img src={chatQuestionIcon} alt="" className="pq-bot-avatar" />
                  <div className="pq-bubble-text">{questionLabel}</div>
                </div>
              </div>

              <div className="pq-input-wrap">
                <div className="pq-input-row">
                  <input
                    ref={inputRef}
                    type="text"
                    className="pq-input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder={currentQuestion.placeholder}
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
                    className="pq-icon-btn pq-icon-btn--send"
                    onClick={handleSubmit}
                    disabled={submitting}
                    title="Send"
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
                    className="pq-submit-btn"
                    onClick={handleSubmit}
                    disabled={submitting}
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
