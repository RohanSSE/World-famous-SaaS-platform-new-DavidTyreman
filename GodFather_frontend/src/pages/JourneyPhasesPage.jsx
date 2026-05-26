import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Lock } from "lucide-react";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import "./JourneyPhasesPage.css";

const PHASES = [
  {
    id: 1,
    questions: "Questions 1–8",
    title: "Foundation & Identity",
    description:
      "Discover the emotional truth, meaning, positioning, and opportunity behind your brand.",
  },
  {
    id: 2,
    questions: "Questions 9–20",
    title: "Differentiation & Strategic Depth",
    description:
      "Define what makes your brand emotionally meaningful, memorable, and difficult to ignore.",
  },
  {
    id: 3,
    questions: "Questions 21–30",
    title: "Alignment & Brand Expansion",
    description:
      "Transform your insights into a strategically aligned Brand Book and long-term growth foundation.",
  },
];

export default function JourneyPhasesPage() {
  const navigate = useNavigate();
  const [activePhase, setActivePhase] = useState(1);

  const handleGoDeeper = () => navigate("/stepper");
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
          {PHASES.map((phase) => {
            const isActive = activePhase === phase.id;
            const isLocked = phase.id > 1;
            return (
              <article
                key={phase.id}
                className={`journey-phase-card ${isActive ? "active" : ""} ${isLocked ? "locked" : ""}`}
                onClick={() => setActivePhase(phase.id)}
                onKeyDown={(e) => e.key === "Enter" && setActivePhase(phase.id)}
                role="button"
                tabIndex={0}
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

        <button type="button" className="journey-phases-cta" onClick={handleGoDeeper}>
          Let&apos;s Go Deeper
        </button>
      </main>
    </div>
  );
}
