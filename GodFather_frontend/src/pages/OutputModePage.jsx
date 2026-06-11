import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import "./OutputModePage.css";

const PROMOTION_STARTER_STORAGE_KEY = "brandPromotionStarter";

const UNDERSTANDING_POINTS = [
  "Your positioning",
  "Your customers",
  "Your values",
  "Your emotional strengths",
  "Your opportunities for differentiation",
];

const STARTING_POINTS = [
  "Create A Social Media Campaign",
  "Build Community Around My Brand",
  "Create Customer Excitement",
  "Strengthen My Positioning",
  "Improve My Messaging",
  "Generate Referral Opportunities",
  "Create Thought Leadership Content",
  "Improve My Brand Story",
  "Launch A Promotion",
  "Build Customer Trust",
  "Increase Visibility",
  "Develop Strategic Partnerships",
  "Create A Seasonal Campaign",
];

function buildPromotionPrompt(startingPoint) {
  return [
    `The user selected this Brand Promotion Phase starting point: ${startingPoint}.`,
    "Use the completed Brand Book, session answers, positioning, customer insights, values, emotional strengths, and differentiation opportunities as the source of truth.",
    "Respond as the Brand Godfather in a strategic, practical way. Start by acknowledging the selected objective, then give a clear first direction the user can act on.",
    "Include one strategic angle, three practical first moves, and one sharp follow-up question that helps refine the next response.",
    "Keep the answer aligned with the brand. Avoid generic marketing advice, random tactics, viral/growth-hack language, or anything that conflicts with the Brand Book.",
  ].join("\n");
}

export default function OutputModePage() {
  const navigate = useNavigate();

  const handleStartingPoint = (startingPoint) => {
    const promotionStarter = {
      id: `promotion-${Date.now()}`,
      goal: startingPoint,
      prompt: buildPromotionPrompt(startingPoint),
    };

    try {
      sessionStorage.setItem(PROMOTION_STARTER_STORAGE_KEY, JSON.stringify(promotionStarter));
    } catch {
      // Route state still carries the selected starter for the next page.
    }

    navigate("/output-chat", { state: { promotionStarter } });
  };

  return (
    <div className="omp-page">
      <header className="omp-topbar">
        <ChatNavbar
          showSaveButton={false}
          showDownloadButton={false}
          showLogoutButton
          phaseStatus={{
            title: "Brand Promotion Phase",
            subtitle: "Brand Book complete · Promotion strategy ready",
            progress: 100,
          }}
        />
      </header>

      <main className="omp-main">
        <button type="button" className="omp-back" onClick={() => navigate("/brand-book-ready")}>
          Back
        </button>

        <div className="omp-shell">
          <section className="omp-promo-copy" aria-label="Brand Promotion Phase introduction">
            <span className="omp-kicker">Output Mode</span>
            <h1>
              <span>Welcome To The Brand</span>
              <span>Promotion Phase</span>
            </h1>
            <p className="omp-lead">Your Brand Book has given me a deep understanding of:</p>

            <ul className="omp-understanding-list">
              {UNDERSTANDING_POINTS.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>

            <div className="omp-copy-stack">
              <p>
                From this point forward, I can help you create campaigns, content, messaging,
                customer experiences, community-building ideas, thought leadership, promotional
                strategies, and growth opportunities that remain aligned with your brand.
              </p>
              <p>
                The strongest brands do not grow through random marketing. They grow through
                consistent, strategic communication.
              </p>
              <p>My role now is to help you become the go-to brand in your market.</p>
              <p>Let&apos;s begin.</p>
            </div>
          </section>

          <section className="omp-orb-guide" aria-label="Choose a Brand Promotion starting point">
            <div className="omp-guide-orb" aria-hidden="true">
              <OrbPresence>
                <BrandOrb size="welcome" />
              </OrbPresence>
            </div>

            <div className="omp-choice-bubble">
              <span className="omp-bubble-tail" aria-hidden="true" />
              <p className="omp-guided-heading">Choose A Starting Point</p>
              <div className="omp-pill-wrap">
                {STARTING_POINTS.map((point) => (
                  <button
                    key={point}
                    type="button"
                    className="omp-pill"
                    onClick={() => handleStartingPoint(point)}
                  >
                    {point}
                  </button>
                ))}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
