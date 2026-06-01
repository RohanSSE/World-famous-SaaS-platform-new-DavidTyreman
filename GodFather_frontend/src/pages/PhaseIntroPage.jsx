import { useNavigate, useParams, Navigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import { getJourneyPhase, isPhaseUnlocked } from "../constants/journeyPhases";
import "./PhaseIntroPage.css";

export default function PhaseIntroPage() {
  const navigate = useNavigate();
  const { phaseId } = useParams();
  const phase = getJourneyPhase(phaseId);

  if (!phase || !isPhaseUnlocked(phase.id)) {
    return <Navigate to="/journey-phases" replace />;
  }

  const handleStart = () => navigate(`/phase-questions/${phase.id}`);
  const handleBack = () => navigate("/journey-phases");
  const handleNext = () => handleStart();

  return (
    <div className="phase-intro-page">
      <div className="phase-intro-vignette" aria-hidden="true" />
      <div className="phase-intro-glow phase-intro-glow--left" aria-hidden="true" />
      <div className="phase-intro-glow phase-intro-glow--center" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        onNext={handleNext}
      />

      <main className="phase-intro-main">
        <BrandOrb size="welcome" className="phase-intro-orb" />

        <h1 className="phase-intro-title">{phase.intro.headline}</h1>

        <div className="phase-intro-body">
          {phase.intro.bodyLines.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>

        <button type="button" className="phase-intro-cta" onClick={handleStart}>
          Let&apos;s Start
        </button>
      </main>
    </div>
  );
}
