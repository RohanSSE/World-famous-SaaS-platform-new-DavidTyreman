import { useNavigate, useParams, Navigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import {
  getJourneyPhase,
  isPhaseUnlocked,
  JOURNEY_PHASES,
} from "../constants/journeyPhases";
import "./PhaseCompletePage.css";

function SparkleIcon() {
  return (
    <div className="pc-sparkle" aria-hidden="true">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <path
          d="M24 4L26.2 20.8L43 24L26.2 27.2L24 44L21.8 27.2L5 24L21.8 20.8L24 4Z"
          fill="url(#pc-sparkle-grad)"
        />
        <defs>
          <linearGradient id="pc-sparkle-grad" x1="5" y1="4" x2="43" y2="44">
            <stop stopColor="#8ee5ff" />
            <stop offset="1" stopColor="#3959e5" />
          </linearGradient>
        </defs>
      </svg>
      <span className="pc-sparkle-dot pc-sparkle-dot--1">+</span>
      <span className="pc-sparkle-dot pc-sparkle-dot--2">+</span>
      <span className="pc-sparkle-dot pc-sparkle-dot--3">·</span>
    </div>
  );
}

export default function PhaseCompletePage() {
  const navigate = useNavigate();
  const { phaseId } = useParams();
  const phase = getJourneyPhase(phaseId);
  const complete = phase?.complete;

  if (!phase || !complete || !isPhaseUnlocked(phase.id)) {
    return <Navigate to="/journey-phases" replace />;
  }

  const nextPhaseId = phase.id + 1;
  const hasNextPhase = nextPhaseId <= JOURNEY_PHASES.length;

  const handleContinue = () => {
    if (hasNextPhase && isPhaseUnlocked(nextPhaseId)) {
      navigate(`/phase-questions/${nextPhaseId}`);
      return;
    }
    navigate("/brand-summary");
  };

  const handleBack = () => navigate(`/phase-questions/${phase.id}`);

  return (
    <div className="phase-complete-page">
      <div className="phase-complete-vignette" aria-hidden="true" />
      <div className="phase-complete-glow" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        showNext={false}
      />

      <main className="phase-complete-main">
        <article className="phase-complete-card">
          <SparkleIcon />

          <h1 className="phase-complete-title">{complete.title}</h1>
          <p className="phase-complete-subtitle">{complete.subtitle}</p>

          {!complete.minimal && (
            <div className="phase-complete-body">
              <p className="phase-complete-lead">{complete.understandingTitle}</p>
              <ul className="phase-complete-list">
                {(complete.bullets || []).map((item) => (
                  <li key={item}>
                    <span className="phase-complete-arrow" aria-hidden="true">
                      →
                    </span>
                    {item}
                  </li>
                ))}
              </ul>
              <p className="phase-complete-next">{complete.nextText}</p>
            </div>
          )}

          <div className="phase-complete-progress-wrap">
            <div className="phase-complete-progress-track">
              <div
                className="phase-complete-progress-fill"
                style={{ width: `${complete.progressPercent}%` }}
              />
            </div>
            <p className="phase-complete-progress-label">
              {complete.progressPercent}% Complete
            </p>
          </div>

          <button type="button" className="phase-complete-cta" onClick={handleContinue}>
            {complete.ctaLabel} →
          </button>
        </article>
      </main>
    </div>
  );
}
