import OnboardingHeader from "./OnboardingHeader";
import "./OnboardingNavBar.css";

/**
 * Shared onboarding top bar: THE GODFATHER logo + avatar + Back/Next pills (Welcome layout).
 */
export default function OnboardingNavBar({
  onLogoClick,
  onBack,
  onNext,
  showBack = true,
  showNext = true,
  backLabel = "Back",
  nextLabel = "Next",
}) {
  return (
    <>
      <OnboardingHeader onLogoClick={onLogoClick} />
      {(showBack || showNext) && (
        <div className="onboarding-nav-row">
          {showBack ? (
            <button type="button" className="onboarding-pill-btn" onClick={onBack}>
              {backLabel}
            </button>
          ) : (
            <span className="onboarding-nav-spacer" aria-hidden="true" />
          )}
          {showNext ? (
            <button type="button" className="onboarding-pill-btn" onClick={onNext}>
              {nextLabel}
            </button>
          ) : (
            <span className="onboarding-nav-spacer" aria-hidden="true" />
          )}
        </div>
      )}
    </>
  );
}
