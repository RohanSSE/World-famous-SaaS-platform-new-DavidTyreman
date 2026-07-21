import { useState } from "react";
import { useNavigate } from "react-router-dom";
import OnboardingNavBar from "../components/onboarding/OnboardingNavBar";
import BrandOrb from "../components/orb/BrandOrb";
import useTypewriter from "../hooks/useTypewriter";
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

const HEADER_COPY = {
  title: "Before We Continue",
  subtitle: "A few things will help you get the most from this journey.",
};

const CHAT_COPY = {
  lead: "As we progress, I'll begin learning:",
  items: [
    "how you think",
    "what matters to you",
    "what your customers truly value",
    "where your greatest opportunities exist",
  ],
  body:
    "You're not simply answering questions. You're learning to think about your business the way strong brands do. It also helps make sure your answers work together clearly and consistently so your brand becomes more focused, differentiated, and memorable with every step.",
};

const REMEMBER_COPY = {
  title: "Remember:",
  body:
    "There are no perfect answers here — only more honest, more strategic, and more powerful ones. The more authentic you are, the more valuable this process becomes.",
};

const HEADER_TITLE_STEP = 0;
const HEADER_SUBTITLE_STEP = 1;
const CARD_START_STEP = 2;
const CHAT_STEP = CARD_START_STEP + GUIDE_CARDS.length;
const REMEMBER_STEP = CHAT_STEP + 1;
const TYPE_STEPS = [
  HEADER_COPY.title,
  HEADER_COPY.subtitle,
  ...GUIDE_CARDS.map((card) => `${card.title}\n${card.body}`),
  `${CHAT_COPY.lead}\n${CHAT_COPY.items.join("\n")}\n\n${CHAT_COPY.body}`,
  `${REMEMBER_COPY.title}\n${REMEMBER_COPY.body}`,
];

function splitHeadingBody(text) {
  const [heading = "", ...bodyLines] = text.split("\n");

  return {
    heading,
    body: bodyLines.join("\n"),
  };
}

function splitChatText(text) {
  const lines = text.split("\n");

  return {
    lead: lines[0] || "",
    items: lines.slice(1, 5),
    body: lines.slice(6).join("\n"),
  };
}

export default function BeforeContinuePage() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const currentStepText = TYPE_STEPS[activeStep] || "";
  const { display, isTyping } = useTypewriter(currentStepText, {
    speed: activeStep === HEADER_TITLE_STEP ? 74 : 34,
    commaPause: 150,
    punctuationPause: 360,
    enabled: activeStep < TYPE_STEPS.length,
    onComplete: () => setActiveStep((step) => Math.min(step + 1, TYPE_STEPS.length)),
  });
  const isStepReady = (step) => activeStep >= step;
  const isSequenceComplete = activeStep >= TYPE_STEPS.length;
  const getStepText = (step) => {
    if (activeStep > step) return TYPE_STEPS[step] || "";
    if (activeStep === step) return display;
    return "";
  };
  const typedTitle = getStepText(HEADER_TITLE_STEP);
  const typedSubtitle = getStepText(HEADER_SUBTITLE_STEP);
  const typedChat = splitChatText(getStepText(CHAT_STEP));
  const typedRemember = splitHeadingBody(getStepText(REMEMBER_STEP));

  const handleDiscover = () => {
    if (!isSequenceComplete) return;

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
            <h1 className="before-continue-title">
              {typedTitle}
              {activeStep === HEADER_TITLE_STEP && isTyping ? (
                <span className="before-continue-type-cursor" aria-hidden="true" />
              ) : null}
            </h1>
            <p className="before-continue-subtitle">
              {typedSubtitle}
              {activeStep === HEADER_SUBTITLE_STEP && isTyping ? (
                <span className="before-continue-type-cursor" aria-hidden="true" />
              ) : null}
            </p>
          </header>

          <aside className="before-continue-orb-stage before-continue-orb-breeze" aria-label="ORB companion">
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
          {GUIDE_CARDS.map((card, index) => {
            const step = CARD_START_STEP + index;
            const typedCard = splitHeadingBody(getStepText(step));

            return isStepReady(step) ? (
              <article key={card.title} className="before-continue-card" style={{ "--card-index": index }}>
                <h2>
                  {typedCard.heading}
                  {activeStep === step && isTyping && !typedCard.body ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </h2>
                <p>
                  {typedCard.body}
                  {activeStep === step && isTyping && typedCard.body ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </p>
              </article>
            ) : null;
          })}
        </section>

        {isStepReady(CHAT_STEP) ? (
          <section className="before-continue-chat" aria-label="ORB guidance">
            <div className="before-continue-bubble-content before-continue-tail-right">
              <div>
                <p className="before-continue-bubble-lead">
                  {typedChat.lead}
                  {activeStep === CHAT_STEP && isTyping && typedChat.items.length === 0 ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </p>
                <ul className="before-continue-list">
                  {typedChat.items.map((item, index) => (
                    <li key={`${CHAT_COPY.items[index]}-${index}`}>
                      {item}
                      {activeStep === CHAT_STEP && isTyping && index === typedChat.items.length - 1 && !typedChat.body ? (
                        <span className="before-continue-type-cursor" aria-hidden="true" />
                      ) : null}
                    </li>
                  ))}
                </ul>
                <p className="before-continue-bubble-body">
                  {typedChat.body}
                  {activeStep === CHAT_STEP && isTyping && typedChat.body ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </p>
              </div>
              <div className="before-continue-mini-signal" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
            </div>

            {isStepReady(REMEMBER_STEP) ? (
              <div className="before-continue-remember-card">
                <h3>
                  {typedRemember.heading}
                  {activeStep === REMEMBER_STEP && isTyping && !typedRemember.body ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </h3>
                <p className="before-continue-bubble-body">
                  {typedRemember.body}
                  {activeStep === REMEMBER_STEP && isTyping && typedRemember.body ? (
                    <span className="before-continue-type-cursor" aria-hidden="true" />
                  ) : null}
                </p>
              </div>
            ) : null}
          </section>
        ) : null}

        {isSequenceComplete ? (
          <footer className="before-continue-footer">
            <button type="button" className="before-continue-cta before-continue-cta--ready" onClick={handleDiscover}>
              Let&apos;s Discover Your Brand
            </button>
          </footer>
        ) : null}
      </main>
    </div>
  );
}
