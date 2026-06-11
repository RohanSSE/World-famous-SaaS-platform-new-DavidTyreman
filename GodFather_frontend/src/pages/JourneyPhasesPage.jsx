import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CreditCard, FileText, Lock } from "lucide-react";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import authService from "../services/authService";
import {
  JOURNEY_PHASES,
  isPhaseSubscriptionLocked,
  isPhaseUnlocked,
  unlockPhaseAfterComplete,
} from "../constants/journeyPhases";
import "./JourneyPhasesPage.css";

export default function JourneyPhasesPage() {
  const navigate = useNavigate();
  const [selectedPhase, setSelectedPhase] = useState(1);
  const [billing, setBilling] = useState(null);
  const [billingError, setBillingError] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await authService.getBillingStatus();
        if (cancelled) return;
        setBilling(data);
        if (data?.has_active_subscription) unlockPhaseAfterComplete(1);
      } catch {
        if (!cancelled) setBilling(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const startCheckout = async () => {
    if (checkoutLoading) return;
    setCheckoutLoading(true);
    setBillingError("");
    try {
      const origin = window.location.origin;
      const returnPhase = Math.max(1, Number(selectedPhase || 2) - 1);
      const data = await authService.createSubscriptionCheckout({
        success_url: `${origin}/phase-complete/${returnPhase}?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${origin}/journey-phases`,
      });
      if (data?.already_active) {
        setBilling(data);
        unlockPhaseAfterComplete(1);
        navigate("/phase-intro/2");
        return;
      }
      if (!data?.checkout_url) throw new Error("Checkout URL missing from server response");
      window.location.href = data.checkout_url;
    } catch (err) {
      setBillingError(err?.message || "Could not start checkout");
      setCheckoutLoading(false);
    }
  };

  const handleGoDeeper = () => {
    if (!selectedPhase) return;
    if (!isPhaseUnlocked(selectedPhase)) {
      if (isPhaseSubscriptionLocked(selectedPhase)) startCheckout();
      return;
    }
    navigate(`/phase-intro/${selectedPhase}`);
  };

  const handleBack = () => navigate("/before-continue");

  return (
    <div className="journey-phases-page">
      <div className="journey-phases-bg-orb" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        showNext={false}
        phaseStatus={{
          title: "Journey phases",
          subtitle: "Choose your next step",
          progress: 20,
        }}
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
            const isSubscriptionLocked = isPhaseSubscriptionLocked(phase.id);
            return (
              <article
                key={phase.id}
                className={`journey-phase-card ${isSelected ? "active" : ""} ${isLocked ? "locked" : ""}`}
                style={{ "--phase-index": phase.id - 1 }}
                onClick={() => {
                  if (isLocked && !isSubscriptionLocked) return;
                  setSelectedPhase(phase.id);
                }}
                onKeyDown={(e) => {
                  if (isLocked && !isSubscriptionLocked) return;
                  if (e.key === "Enter") setSelectedPhase(phase.id);
                }}
                role="button"
                tabIndex={isLocked && !isSubscriptionLocked ? -1 : 0}
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

        {selectedPhase && isPhaseSubscriptionLocked(selectedPhase) && (
          <section className="journey-upgrade-panel" aria-live="polite">
            <div className="journey-upgrade-icon" aria-hidden="true">
              <CreditCard size={18} strokeWidth={2} />
            </div>
            <p>
              {billing?.plan
                ? `Upgrade with ${billing.plan.name} · ${billing.plan.price_display}`
                : "Ask admin to add an active subscription plan before continuing."}
            </p>
            {billingError && <p className="journey-upgrade-error">{billingError}</p>}
          </section>
        )}

        <button
          type="button"
          className="journey-phases-cta"
          onClick={handleGoDeeper}
          disabled={!selectedPhase || checkoutLoading || (isPhaseSubscriptionLocked(selectedPhase) && !billing?.plan)}
        >
          {checkoutLoading ? "Opening checkout…" : isPhaseSubscriptionLocked(selectedPhase) ? "Upgrade & Continue" : "Let's Go Deeper"}
        </button>
      </main>
    </div>
  );
}
