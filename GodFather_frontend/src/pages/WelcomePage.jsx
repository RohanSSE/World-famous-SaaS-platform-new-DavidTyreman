import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import "./WelcomePage.css";

export default function WelcomePage() {
  const navigate = useNavigate();

  const handleBegin = () => {
    navigate("/brand-intro");
  };

  const handleBack = () => {
    navigate("/intro-ductory");
  };

  const handleNext = () => {
    navigate("/brand-intro");
  };

  return (
    <div className="welcome-page">
      <div className="welcome-page-vignette" aria-hidden="true" />

      <OnboardingNavBar
        onLogoClick={() => navigate("/welcome")}
        onBack={handleBack}
        onNext={handleNext}
        showNext={false}
        phaseStatus={{
          title: "Welcome",
          subtitle: "Brand journey ready",
          progress: 5,
        }}
      />

      <main className="welcome-main">
        <BrandOrb size="welcome" className="welcome-brand-orb" />

        <h1 className="welcome-title">Welcome</h1>

        <p className="welcome-lead">
          If you&apos;ve ever wanted expert guidance to help your business stand out, grow stronger,
          and become the go-to brand in your market, you&apos;re in the right place.
        </p>

        <p className="welcome-body">
          I&apos;m the <strong>Brand Godfather</strong>, and I&apos;m here to help you think
          differently about your business, your customers, and the meaning behind your brand.
        </p>

        <button type="button" className="welcome-cta" onClick={handleBegin}>
          Let&apos;s Begin
        </button>
      </main>
    </div>
  );
}
