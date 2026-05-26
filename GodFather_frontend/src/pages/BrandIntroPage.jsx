import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import "./BrandIntroPage.css";

const TACTICS = ["Social posts", "Advertising", "Promotions", "Websites", "Funnels"];

const GROUP_139_IMAGE = "/Group_139.svg";

export default function BrandIntroPage() {
  const navigate = useNavigate();

  const handleReady = () => navigate("/before-continue");
  const handleBack = () => navigate("/welcome");
  const handleNext = () => handleReady();

  return (
    <div className="brand-intro-page">
      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        onNext={handleNext}
      />

      <main className="brand-intro-main">
        <section className="brand-intro-hero">
          <div className="brand-intro-orb-wrap" aria-hidden="true">
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

        <section className="brand-intro-cards-row">
          <img
            src={GROUP_139_IMAGE}
            alt="Brand journey overview"
            className="brand-intro-group-image"
          />
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
