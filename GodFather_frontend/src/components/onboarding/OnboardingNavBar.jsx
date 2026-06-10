import OnboardingHeader from "./OnboardingHeader";
import "./OnboardingNavBar.css";

/**
 * Shared onboarding top bar: THE GODFATHER logo + avatar + Back/Next pills (Welcome layout).
 */
export default function OnboardingNavBar({
  onLogoClick,
  onBack,
  onNext,
  logoPath,
  backPath,
  nextPath,
  showBack = true,
  showNext = true,
  backLabel = "Back",
  nextLabel = "Next",
  phaseStatus = null,
}) {
  const safeNavigate = (handler, fallbackPath) => {
    handler?.();
    if (!fallbackPath) return;
    window.setTimeout(() => {
      if (window.location.pathname !== fallbackPath) {
        window.location.assign(fallbackPath);
      }
    }, 140);
  };

  return (
    <>
      <OnboardingHeader onLogoClick={() => safeNavigate(onLogoClick, logoPath)} phaseStatus={phaseStatus} />
      {(showBack || showNext) && (
        <div className="onboarding-nav-row">
          {showBack ? (
            <button
              type="button"
              className="onboarding-pill-btn"
              onClick={() => safeNavigate(onBack, backPath)}
            >
              {backLabel}
            </button>
          ) : (
            <span className="onboarding-nav-spacer" aria-hidden="true" />
          )}
          {showNext ? (
            <button
              type="button"
              className="onboarding-pill-btn"
              onClick={() => safeNavigate(onNext, nextPath)}
            >
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
