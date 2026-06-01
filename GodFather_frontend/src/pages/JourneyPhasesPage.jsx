import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Lock } from "lucide-react";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import { JOURNEY_PHASES, isPhaseUnlocked } from "../constants/journeyPhases";
import "./JourneyPhasesPage.css";

export default function JourneyPhasesPage() {
  const navigate = useNavigate();
  const [selectedPhase, setSelectedPhase] = useState(1);

  const handleGoDeeper = () => {
    if (!selectedPhase) return;
    navigate(`/phase-questions/${selectedPhase}`);
  };

  const handleBack = () => navigate("/before-continue");

  return (
    <div className="journey-phases-page">
      <div className="journey-phases-bg-orb" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        showNext={false}
      />

      <main className="journey-phases-main">
        <div className="journey-phases-intro">
          <div className="journey-phases-orb-wrap" aria-hidden="true">
            <BrandOrb size="md" />
          </div>
          <h1 className="journey-phases-title">The Journey: 3 Phases, 30 Questions</h1>
        </div>

        <section className="journey-phases-cards" aria-label="Journey phases">
          {JOURNEY_PHASES.map((phase) => {
            const isSelected = selectedPhase === phase.id;
            const isLocked = !isPhaseUnlocked(phase.id);
            return (
              <article
                key={phase.id}
                className={`journey-phase-card ${isSelected ? "active" : ""} ${isLocked ? "locked" : ""}`}
                onClick={() => {
                  if (isLocked) return;
                  setSelectedPhase(phase.id);
                }}
                onKeyDown={(e) => {
                  if (isLocked) return;
                  if (e.key === "Enter") setSelectedPhase(phase.id);
                }}
                role="button"
                tabIndex={isLocked ? -1 : 0}
                aria-disabled={isLocked}
              >
                <div className="journey-phase-card-top">
                  <span className="journey-phase-num">{phase.id}</span>
                  <span className="journey-phase-meta">
                    {isLocked ? (
                      <Lock size={14} strokeWidth={2} aria-hidden />
                    ) : (
                      <FileText size={14} strokeWidth={2} aria-hidden />
                    )}
                    {phase.questions}
                  </span>
                </div>
                <h2>{phase.title}</h2>
                <p>{phase.description}</p>
              </article>
            );
          })}
        </section>

        <button
          type="button"
          className="journey-phases-cta"
          onClick={handleGoDeeper}
          disabled={!selectedPhase}
        >
          Let&apos;s Go Deeper
        </button>
      </main>
    </div>
  );
}
