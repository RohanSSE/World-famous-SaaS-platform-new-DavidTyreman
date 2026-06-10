import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import "./BrandBookReadyPage.css";

const discoveryPoints = [
  "Emotional positioning",
  "Strategic differentiation",
  "Customer psychology",
  "Messaging opportunities",
  "Brand voice",
  "Growth direction",
  "Deeper strategic alignment",
];

const outputPoints = [
  "Ask sharper brand questions",
  "Request refinements",
  "Strengthen positioning",
  "Explore new opportunities",
  "Generate strategic campaigns",
  "Create storytelling ideas",
  "Build community engagement",
  "Develop promotional concepts",
  "Create thought leadership",
  "Keep evolving your brand over time",
];

export default function BrandBookReadyPage() {
  const navigate = useNavigate();

  const sessionTitle = (() => {
    try {
      const raw = localStorage.getItem("session");
      const parsed = raw ? JSON.parse(raw) : null;
      return parsed?.title || "Your Brand";
    } catch {
      return "Your Brand";
    }
  })();

  return (
    <div className="bbr-page">
      <header className="bbr-topbar">
        <ChatNavbar
          showSaveButton={false}
          showDownloadButton={false}
          showLogoutButton
          phaseStatus={{
            title: "Brand Book ready",
            subtitle: "Discovery complete · Output mode is ready",
            progress: 100,
          }}
        />
      </header>

      <main className="bbr-main">
        <button
          type="button"
          className="bbr-back"
          onClick={() => navigate("/brand-summary", { state: { page: 0 } })}
        >
          Back
        </button>

        <h1>Your Brand Book Is Ready</h1>
        <p>
          Your Brand Book is designed to become the strategic foundation behind your messaging,
          positioning, customer experience, content, campaigns, and long-term growth.
          From this point forward, the Brand Godfather can help you:
        </p>

        <div className="bbr-cards">
          <article className="bbr-card">
            <div className="bbr-card-heading">
              <h3>You&apos;ll Discover</h3>
            </div>
            <ul className="bbr-list">
              {discoveryPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
            <p className="bbr-card-note">And this is only the beginning.</p>
          </article>

          <article className="bbr-card">
            <div className="bbr-card-heading">
              <h3>You Can Now</h3>
            </div>
            <ul className="bbr-list">
              {outputPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </article>
        </div>

        <p className="bbr-foot">Strong brands are not static. They evolve, deepen, and strengthen continuously.</p>

        <button type="button" className="bbr-cta" onClick={() => navigate("/output-mode")}>
          Enter Output Mode
        </button>
      </main>

      <div className="bbr-orb" aria-hidden="true">
        <OrbPresence>
          <BrandOrb size="welcome" />
        </OrbPresence>
      </div>

      <div className="bbr-session-tag">{sessionTitle}</div>
    </div>
  );
}
