import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import "./BrandIntroPage.css";

const TACTICS = ["Social posts", "Advertising", "Promotions", "Websites", "Funnels"];

const ORB_PROMPTS = [
  "Sometimes I'll challenge your thinking",
  "Sometimes I'll help you dig deeper",
  "Sometimes I'll recognize an insight worth building around",
];

export default function BrandIntroPage() {
  const navigate = useNavigate();

  const handleReady = () => {
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
          <div className="brand-intro-orb-wrap" aria-hidden="true">
            <span className="brand-intro-orb-ring" />
            <BrandOrb size="hero" />
          </div>
          <h1 className="brand-intro-heading">Hi, I am The Brand Godfather</h1>
          <p className="brand-intro-sub brand-intro-subheading">
            Most businesses focus on tactics first:
          </p>
          <div className="brand-intro-tactics">
            {TACTICS.map((t) => (
              <span key={t} className="brand-intro-tactic-pill">
                {t}
              </span>
            ))}
          </div>
        </section>

        <section className="brand-intro-discovery-grid" aria-label="Brand discovery orientation">
          <article className="brand-intro-principle-card brand-intro-reveal-card">
            <span className="brand-intro-card-kicker">Discovery starts here</span>
            <p>
              But long-term success starts with mindset. Strong brands think differently from the
              very beginning.
            </p>
            <strong>That’s why this experience starts with discovery.</strong>
          </article>

          <article className="brand-intro-orb-card brand-intro-reveal-card">
            <span className="brand-intro-card-kicker">How the ORB works</span>
            <p>
              Over the next 30 questions, we&apos;ll explore the emotional identity, positioning,
              meaning, and strategic opportunity behind your brand.
            </p>
            <strong>The ORB is how we communicate throughout this journey.</strong>
            <div className="brand-intro-orb-prompts" aria-label="ORB guidance examples">
              {ORB_PROMPTS.map((prompt) => (
                <span key={prompt}>{prompt}</span>
              ))}
            </div>
          </article>
        </section>

        <section className="brand-intro-footer">
          <h2 className="brand-intro-footer-title">Take Your Time</h2>
          <p className="brand-intro-footer-italic">
            Most businesses unknowingly drift into &ldquo;vendor thinking&rdquo; — sounding like
            competitors, blending into the market, and competing mostly on price, features, or
            convenience.
          </p>
          <p className="brand-intro-footer-italic">
            My role is to help you move beyond that thinking and uncover what makes your business
            emotionally meaningful, strategically differentiated, and memorable.
          </p>
          <h3 className="brand-intro-footer-heading">This isn&apos;t a survey.</h3>
          <p className="brand-intro-footer-line brand-intro-footer-italic">
            It&apos;s the beginning of building a stronger brand.
          </p>
          <button type="button" className="brand-intro-cta" onClick={handleReady}>
            I&apos;m Ready To Think Bigger
          </button>
        </section>
      </main>
    </div>
  );
}
