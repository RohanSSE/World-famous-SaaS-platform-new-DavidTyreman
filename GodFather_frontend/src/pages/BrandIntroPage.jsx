import { useState } from "react";
import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import useTypewriter from "../hooks/useTypewriter";
import "./BrandIntroPage.css";

const TACTICS = ["Social posts", "Advertising", "Promotions", "Websites", "Funnels"];

const ORB_PROMPTS = [
  "Sometimes I'll challenge your thinking",
  "Sometimes I'll help you dig deeper",
  "Sometimes I'll recognize an insight worth building around",
];

const INTRO_COPY = {
  heading: "Hi, I am The Brand Godfather",
  subheading: "Most businesses focus on tactics first:",
  principle: "But long-term success starts with mindset. Strong brands think differently from the very beginning.",
  principleStrong: "That’s why this experience starts with discovery.",
  orb: "Over the next 30 questions, we'll explore the emotional identity, positioning, meaning, and strategic opportunity behind your brand.",
  orbStrong: "The ORB is how we communicate throughout this journey.",
  footerTitle: "Take Your Time",
  footerOne:
    "Most businesses unknowingly drift into “vendor thinking” — sounding like competitors, blending into the market, and competing mostly on price, features, or convenience.",
  footerTwo:
    "My role is to help you move beyond that thinking and uncover what makes your business emotionally meaningful, strategically differentiated, and memorable.",
  footerHeading: "This isn't a survey.",
  footerLine: "It's the beginning of building a stronger brand.",
};

const TYPEWRITER_OPTIONS = {
  speed: 34,
  commaPause: 150,
  punctuationPause: 360,
};

const advanceTo = (targetStep) => (currentStep) => Math.max(currentStep, targetStep);

export default function BrandIntroPage() {
  const navigate = useNavigate();
  const [typingStep, setTypingStep] = useState(0);
  const isStepReady = (step) => typingStep >= step;

  const { display: typedHeading, isTyping: isHeadingTyping } = useTypewriter(INTRO_COPY.heading, {
    ...TYPEWRITER_OPTIONS,
    speed: 74,
    onComplete: () => setTypingStep(advanceTo(1)),
  });
  const { display: typedSubheading, isTyping: isSubheadingTyping } = useTypewriter(
    isStepReady(1) ? INTRO_COPY.subheading : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(2)),
    },
  );
  const { display: typedPrinciple, isTyping: isPrincipleTyping } = useTypewriter(
    isStepReady(2) ? INTRO_COPY.principle : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(3)),
    },
  );
  const { display: typedPrincipleStrong, isTyping: isPrincipleStrongTyping } = useTypewriter(
    isStepReady(3) ? INTRO_COPY.principleStrong : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(4)),
    },
  );
  const { display: typedOrb, isTyping: isOrbTyping } = useTypewriter(
    isStepReady(4) ? INTRO_COPY.orb : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(5)),
    },
  );
  const { display: typedOrbStrong, isTyping: isOrbStrongTyping } = useTypewriter(
    isStepReady(5) ? INTRO_COPY.orbStrong : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(6)),
    },
  );
  const { display: typedFooterTitle, isTyping: isFooterTitleTyping } = useTypewriter(
    isStepReady(6) ? INTRO_COPY.footerTitle : "",
    {
      ...TYPEWRITER_OPTIONS,
      speed: 58,
      onComplete: () => setTypingStep(advanceTo(7)),
    },
  );
  const { display: typedFooterOne, isTyping: isFooterOneTyping } = useTypewriter(
    isStepReady(7) ? INTRO_COPY.footerOne : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(8)),
    },
  );
  const { display: typedFooterTwo, isTyping: isFooterTwoTyping } = useTypewriter(
    isStepReady(8) ? INTRO_COPY.footerTwo : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(9)),
    },
  );
  const { display: typedFooterHeading, isTyping: isFooterHeadingTyping } = useTypewriter(
    isStepReady(9) ? INTRO_COPY.footerHeading : "",
    {
      ...TYPEWRITER_OPTIONS,
      speed: 56,
      onComplete: () => setTypingStep(advanceTo(10)),
    },
  );
  const { display: typedFooterLine, isTyping: isFooterLineTyping } = useTypewriter(
    isStepReady(10) ? INTRO_COPY.footerLine : "",
    {
      ...TYPEWRITER_OPTIONS,
      onComplete: () => setTypingStep(advanceTo(11)),
    },
  );

  const isReadyToContinue = isStepReady(11);

  const handleReady = () => {
    if (!isReadyToContinue) return;

    // Fallback hard navigation to avoid occasional client-side route freeze.
    navigate("/before-continue");
    window.setTimeout(() => {
      if (window.location.pathname === "/brand-intro") {
        window.location.assign("/before-continue");
      }
    }, 120);
  };
  const handleBack = () => navigate("/welcome");
  return (
    <div className="brand-intro-page">
      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        logoPath="/welcome"
        backPath="/welcome"
        showNext={false}
        phaseStatus={{
          title: "Brand discovery",
          subtitle: "Orientation in progress",
          progress: 10,
        }}
      />

      <main className="brand-intro-main">
        <div className="brand-intro-ambient brand-intro-ambient-left" aria-hidden="true" />
        <div className="brand-intro-ambient brand-intro-ambient-right" aria-hidden="true" />

        <section className="brand-intro-hero">
          <div className="brand-intro-orb-wrap brand-intro-orb-breeze" aria-hidden="true">
            <span className="brand-intro-orb-ring" />
            <BrandOrb size="hero" />
          </div>
          <h1 className="brand-intro-heading" aria-live="polite">
            {typedHeading}
            {isHeadingTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
          </h1>
          <p className="brand-intro-sub brand-intro-subheading">
            {typedSubheading}
            {isSubheadingTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
          </p>
          <div className={`brand-intro-tactics ${isStepReady(2) ? "brand-intro-tactics--ready" : ""}`}>
            {TACTICS.map((t) => (
              <span key={t} className="brand-intro-tactic-pill">
                {t}
              </span>
            ))}
          </div>
        </section>

        <section className="brand-intro-discovery-grid" aria-label="Brand discovery orientation">
          {isStepReady(2) ? (
            <article className="brand-intro-principle-card brand-intro-reveal-card brand-intro-reveal-card--ready">
              <span className="brand-intro-card-kicker">Discovery starts here</span>
              <p>
                {typedPrinciple}
                {isPrincipleTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
              </p>
              <strong>
                {typedPrincipleStrong}
                {isPrincipleStrongTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
              </strong>
            </article>
          ) : null}

          {isStepReady(4) ? (
            <article className="brand-intro-orb-card brand-intro-reveal-card brand-intro-reveal-card--ready">
              <span className="brand-intro-card-kicker">How the ORB works</span>
              <p>
                {typedOrb}
                {isOrbTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
              </p>
              <strong>
                {typedOrbStrong}
                {isOrbStrongTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
              </strong>
              <div
                className={`brand-intro-orb-prompts ${isStepReady(6) ? "brand-intro-orb-prompts--ready" : ""}`}
                aria-label="ORB guidance examples"
              >
                {ORB_PROMPTS.map((prompt) => (
                  <span key={prompt}>{prompt}</span>
                ))}
              </div>
            </article>
          ) : null}
        </section>

        {isStepReady(6) ? (
          <section className="brand-intro-footer">
            <h2 className="brand-intro-footer-title">
              {typedFooterTitle}
              {isFooterTitleTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
            </h2>
            <p className="brand-intro-footer-italic">
              {typedFooterOne}
              {isFooterOneTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
            </p>
            <p className="brand-intro-footer-italic">
              {typedFooterTwo}
              {isFooterTwoTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
            </p>
            <h3 className="brand-intro-footer-heading">
              {typedFooterHeading}
              {isFooterHeadingTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
            </h3>
            <p className="brand-intro-footer-line brand-intro-footer-italic">
              {typedFooterLine}
              {isFooterLineTyping ? <span className="brand-intro-type-cursor" aria-hidden="true" /> : null}
            </p>
            <div className="brand-intro-cta-slot">
              {isReadyToContinue ? (
                <button type="button" className="brand-intro-cta brand-intro-cta--ready" onClick={handleReady}>
                  I&apos;m Ready To Think Bigger
                </button>
              ) : null}
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
