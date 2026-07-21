import { useState } from "react";
import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import useTypewriter from "../hooks/useTypewriter";
import "./WelcomePage.css";

const leadText =
  "If you've ever wanted expert guidance to help your business stand out, grow stronger, and become the go-to brand in your market, you're in the right place.";

const bodyText =
  "I'm the Brand Godfather, and I'm here to help you think differently about your business, your customers, and the meaning behind your brand.";

const welcomeCopy = `${leadText}\n\n${bodyText}`;
const welcomeTitle = "Welcome";
const brandName = "Brand Godfather";
const brandNameStart = bodyText.indexOf(brandName);
const brandNameEnd = brandNameStart + brandName.length;

function renderBodyText(text) {
  if (!text) return null;

  if (text.length <= brandNameStart) return text;

  return (
    <>
      {text.slice(0, brandNameStart)}
      <strong>{text.slice(brandNameStart, Math.min(text.length, brandNameEnd))}</strong>
      {text.length > brandNameEnd ? text.slice(brandNameEnd) : null}
    </>
  );
}

export default function WelcomePage() {
  const navigate = useNavigate();
  const [isTitleComplete, setIsTitleComplete] = useState(false);
  const [isBeginReady, setIsBeginReady] = useState(false);
  const { display: typedTitle, isTyping: isTitleTyping } = useTypewriter(welcomeTitle, {
    speed: 95,
    enabled: true,
    onComplete: () => setIsTitleComplete(true),
  });
  const { display, isTyping } = useTypewriter(isTitleComplete ? welcomeCopy : "", {
    speed: 42,
    commaPause: 170,
    punctuationPause: 420,
    onComplete: () => setIsBeginReady(true),
  });
  const [typedLead = "", typedBody = ""] = display.split("\n\n");

  const handleBegin = () => {
    if (!isBeginReady) return;

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
        <BrandOrb size="welcome" className="welcome-brand-orb welcome-orb-breeze" />

        <h1 className="welcome-title" aria-live="polite">
          {typedTitle}
          {isTitleTyping ? <span className="welcome-type-cursor" aria-hidden="true" /> : null}
        </h1>

        <p className="welcome-lead" aria-live="polite">
          {typedLead}
        </p>

        <p className="welcome-body">
          {renderBodyText(typedBody)}
          {isTyping ? <span className="welcome-type-cursor" aria-hidden="true" /> : null}
        </p>

        <div className="welcome-cta-slot">
          {isBeginReady ? (
            <button type="button" className="welcome-cta welcome-cta--ready" onClick={handleBegin}>
              Let&apos;s Begin
            </button>
          ) : null}
        </div>
      </main>
    </div>
  );
}
