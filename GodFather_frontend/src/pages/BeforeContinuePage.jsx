import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import "./BeforeContinuePage.css";

const GUIDE_CARDS = [
  {
    title: "Be real",
    body: "The strongest brands are built from honesty, clarity, and emotional truth — not polished answers.",
  },
  {
    title: "Take your time",
    body: "This process is designed to help uncover your true unique value and strategic opportunity.",
  },
  {
    title: "Think deeper than most businesses do",
    body: "If an answer sounds too familiar, too generic, or too similar to what others in your market might say, I'll help guide you toward something stronger and more differentiated.",
  },
  {
    title: "The ORB is how we communicate",
    body: "Throughout this journey, the ORB is how I'll communicate with you as the Brand Godfather — guiding your thinking, uncovering stronger insights, and helping shape a more powerful brand direction.",
  },
];

const ORB_CUES = ["Listen", "Challenge", "Clarify"];

export default function BeforeContinuePage() {
  const navigate = useNavigate();

  const handleDiscover = () => {
    navigate("/journey-phases");
    window.setTimeout(() => {
      if (window.location.pathname === "/before-continue") {
        window.location.assign("/journey-phases");
      }
    }, 120);
  };
  const handleBack = () => navigate("/brand-intro");

  return (
    <div className="before-continue-page">
      <div className="before-continue-bg-orb before-continue-bg-orb-1" aria-hidden="true" />
      <div className="before-continue-bg-orb before-continue-bg-orb-2" aria-hidden="true" />
      <div className="before-continue-grid-glow" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        logoPath="/welcome"
        backPath="/brand-intro"
        showNext={false}
        phaseStatus={{
          title: "Before we continue",
          subtitle: "Discovery setup",
          progress: 15,
        }}
      />

      <main className="before-continue-main">
        <section className="before-continue-hero">
          <header className="before-continue-header">
            <span className="before-continue-kicker">Discovery rules</span>
            <h1 className="before-continue-title">Before We Continue</h1>
            <p className="before-continue-subtitle">
              A few things will help you get the most from this journey.
            </p>
          </header>

          <aside className="before-continue-orb-stage" aria-label="ORB companion">
            <span className="before-continue-orb-ring" aria-hidden="true" />
            <span className="before-continue-orb-scan" aria-hidden="true" />
            <BrandOrb size="hero" className="before-continue-hero-orb" />
            <div className="before-continue-orb-cues" aria-hidden="true">
              {ORB_CUES.map((cue) => (
                <span key={cue}>{cue}</span>
              ))}
            </div>
          </aside>
        </section>

        <section className="before-continue-grid" aria-label="Guidelines">
          {GUIDE_CARDS.map((card, index) => (
            <article key={card.title} className="before-continue-card" style={{ "--card-index": index }}>
              <h2>{card.title}</h2>
              <p>{card.body}</p>
            </article>
          ))}
        </section>

        <section className="before-continue-chat" aria-label="ORB guidance">
          <div className="before-continue-bubble-content before-continue-tail-right">
            <div>
              <p className="before-continue-bubble-lead">As we progress, I&apos;ll begin learning:</p>
              <ul className="before-continue-list">
                <li>how you think</li>
                <li>what matters to you</li>
                <li>what your customers truly value</li>
                <li>where your greatest opportunities exist</li>
              </ul>
              <p className="before-continue-bubble-body">
                You&apos;re not simply answering questions. You&apos;re learning to think about your
                business the way strong brands do. It also helps make sure your answers work
                together clearly and consistently so your brand becomes more focused,
                differentiated, and memorable with every step.
              </p>
            </div>
            <div className="before-continue-mini-signal" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          </div>

          <div className="before-continue-remember-card">
            <h3>Remember:</h3>
            <p className="before-continue-bubble-body">
              There are no perfect answers here — only more honest, more strategic, and more
              powerful ones. The more authentic you are, the more valuable this process becomes.
            </p>
          </div>
        </section>

        <footer className="before-continue-footer">
          <button type="button" className="before-continue-cta" onClick={handleDiscover}>
            Let&apos;s Discover Your Brand
          </button>
        </footer>
      </main>
    </div>
  );
}
