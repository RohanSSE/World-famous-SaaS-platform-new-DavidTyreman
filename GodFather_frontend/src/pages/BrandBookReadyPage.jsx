import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import "./BrandBookReadyPage.css";

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
            <h3>Inside, you&apos;ll discover</h3>
            <ul>
              <li>your emotional positioning</li>
              <li>strategic differentiation</li>
              <li>customer psychology</li>
              <li>messaging opportunities</li>
              <li>brand voice</li>
              <li>growth direction</li>
              <li>deeper strategic alignment</li>
            </ul>
            <p>And this is only the beginning.</p>
          </article>

          <article className="bbr-card">
            <h3>You can now:</h3>
            <ul>
              <li>ask questions</li>
              <li>request refinements</li>
              <li>strengthen positioning</li>
              <li>explore new opportunities</li>
              <li>generate strategic campaigns</li>
              <li>create storytelling ideas</li>
              <li>build community engagement</li>
              <li>develop promotional concepts</li>
              <li>create thought leadership</li>
              <li>continue evolving your brand over time</li>
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
