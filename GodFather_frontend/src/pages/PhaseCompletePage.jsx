import { useEffect, useState } from "react";
import { useNavigate, useParams, Navigate, useSearchParams } from "react-router-dom";
import ChatNavbar from "./ChatNavbar";
import authService from "../services/authService";
import StrategicQuoteMoment from "../components/StrategicQuoteMoment";
import {
  doesPhaseRequireSubscription,
  getJourneyPhase,
  isPhaseUnlocked,
  JOURNEY_PHASES,
  unlockPhaseAfterComplete,
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
  const [searchParams, setSearchParams] = useSearchParams();
  const phase = getJourneyPhase(phaseId);
  const complete = phase?.complete;
  const [billing, setBilling] = useState(null);
  const [billingLoading, setBillingLoading] = useState(false);
  const [billingError, setBillingError] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  if (!phase || !complete || !isPhaseUnlocked(phase.id)) {
    return <Navigate to="/journey-phases" replace />;
  }

  const nextPhaseId = phase.id + 1;
  const hasNextPhase = nextPhaseId <= JOURNEY_PHASES.length;
  const completedPhases = Math.max(0, Math.min(JOURNEY_PHASES.length, Number(phaseId) || 0));
  const isDiscoveryComplete = completedPhases >= JOURNEY_PHASES.length;
  const phaseStatus = {
    title: isDiscoveryComplete ? "Brand Book ready" : `Phase ${phase.id} completed`,
    subtitle: isDiscoveryComplete
      ? "Discovery complete · Generate your Brand Book"
      : `${completedPhases} phase${completedPhases === 1 ? "" : "s"} complete · Next phase is ready`,
    progress: Math.round((completedPhases / JOURNEY_PHASES.length) * 100),
  };
  const nextPhaseNeedsSubscription = hasNextPhase && doesPhaseRequireSubscription(nextPhaseId, billing || undefined);
  const needsUpgrade = nextPhaseNeedsSubscription && !billing?.has_active_subscription;
  const unlockedRewards = complete.minimal
    ? ["Brand Book foundation", "Strategic clarity", "Expansion path"]
    : (complete.bullets || []).slice(0, 3);

  useEffect(() => {
    if (!hasNextPhase) return;

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
        if (data?.has_active_subscription) {
          unlockPhaseAfterComplete(phaseId);
        }
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
  }, [hasNextPhase, phaseId, searchParams, setSearchParams]);

  const handleUpgrade = async () => {
    if (checkoutLoading) return;
    setCheckoutLoading(true);
    setBillingError("");
    try {
      const origin = window.location.origin;
      const data = await authService.createSubscriptionCheckout({
        success_url: `${origin}/phase-complete/${phaseId}?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${origin}/phase-complete/${phaseId}?checkout=cancel`,
      });
      if (data?.already_active) {
        setBilling(data);
        unlockPhaseAfterComplete(phaseId);
        navigate(`/phase-questions/${nextPhaseId}`);
        return;
      }
      if (!data?.checkout_url) throw new Error("Checkout URL missing from server response");
      window.location.href = data.checkout_url;
    } catch (err) {
      setBillingError(err?.message || "Could not start checkout");
      setCheckoutLoading(false);
    }
  };

  const markCurrentSessionComplete = async () => {
    try {
      const sessionId = localStorage.getItem("sessionId");
      if (!sessionId) return;
      const data = await authService.completeSession(sessionId);
      const updatedSession = data?.session;
      if (updatedSession) {
        localStorage.setItem("session", JSON.stringify(updatedSession));
      }
    } catch (err) {
      console.warn("Could not mark onboarding session complete", err);
    }
  };

  const handleContinue = async () => {
    if (needsUpgrade) {
      handleUpgrade();
      return;
    }
    if (billing?.has_active_subscription) {
      unlockPhaseAfterComplete(phaseId);
    }
    if (hasNextPhase && isPhaseUnlocked(nextPhaseId)) {
      navigate(`/phase-questions/${nextPhaseId}`);
      return;
    }
    await markCurrentSessionComplete();
    navigate("/brand-summary");
  };

  const handleBack = () => navigate(`/phase-questions/${phase.id}`);

  return (
    <div className="phase-complete-page">
      <div className="phase-complete-vignette" aria-hidden="true" />
      <div className="phase-complete-glow" aria-hidden="true" />
      <div className="phase-complete-bubble-field" aria-hidden="true">
        {Array.from({ length: 14 }).map((_, index) => (
          <span key={index} className={`phase-complete-ai-bubble phase-complete-ai-bubble--${index + 1}`} />
        ))}
      </div>

      <ChatNavbar showSaveButton={false} showDownloadButton={false} showLogoutButton phaseStatus={phaseStatus} />

      <div className="phase-complete-back-row">
        <button type="button" className="phase-complete-back-btn" onClick={handleBack}>
          Back
        </button>
      </div>

      <main className="phase-complete-main">
        <article className="phase-complete-card">
          <SparkleIcon />
          <div className="phase-complete-level-badge">
            {isDiscoveryComplete ? "Discovery complete" : `Level ${phase.id} complete`}
          </div>

          <h1 className="phase-complete-title">{complete.title}</h1>
          <p className="phase-complete-subtitle">{complete.subtitle}</p>

          <div className="phase-complete-unlocks" aria-label="Unlocked rewards">
            {unlockedRewards.map((item, index) => (
              <div key={item} className="phase-complete-unlock-card" style={{ "--unlock-index": index }}>
                <span>Unlocked</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>

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

          {hasNextPhase && nextPhaseNeedsSubscription && (
            <div className="phase-complete-upgrade" aria-live="polite">
              {billingLoading ? (
                <p>Checking your subscription…</p>
              ) : billing?.has_active_subscription ? (
                <p>Your subscription is active. The next phase is unlocked.</p>
              ) : billing?.plan ? (
                <p>
                  Continue with {billing.plan.name} · {billing.plan.price_display}
                </p>
              ) : (
                <p>Ask admin to add an active subscription plan.</p>
              )}
              {billingError && <p className="phase-complete-error">{billingError}</p>}
            </div>
          )}

          <button
            type="button"
            className="phase-complete-cta"
            onClick={handleContinue}
            disabled={billingLoading || checkoutLoading || (needsUpgrade && !billing?.plan)}
          >
            {checkoutLoading ? "Opening checkout…" : needsUpgrade ? "Upgrade & Continue →" : `${complete.ctaLabel} →`}
          </button>
        </article>
      </main>

      <StrategicQuoteMoment
        context={isDiscoveryComplete ? "brand_book_loading" : "phase_complete"}
        phaseId={phase.id}
        variant="overlay"
        eyebrow={isDiscoveryComplete ? "Before the Brand Book" : "Between phases"}
        storageKey={`phase-complete-quote-${phase.id}`}
      />
    </div>
  );
}
