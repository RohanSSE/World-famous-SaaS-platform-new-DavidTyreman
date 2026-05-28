import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import "./OutputChatPage.css";

export default function OutputChatPage() {
  const navigate = useNavigate();

  return (
    <div className="ocp-page">
      <header className="ocp-topbar">
        <ChatNavbar
          showSaveButton={false}
          showDownloadButton={false}
          showLogoutButton
        />
      </header>

      <main className="ocp-main">
        <div className="ocp-row">
          <button type="button" className="ocp-chip" onClick={() => navigate("/output-mode")}>
            Back
          </button>
          <button type="button" className="ocp-chip" onClick={() => navigate("/brand-summary")}>
            Exit
          </button>
        </div>

        <div className="ocp-bubble">
          <span className="ocp-dot" />
          <p>
            I&apos;m here to help you think strategically. Ask me anything about positioning,
            messaging, campaigns, or how to apply your brand identity.
          </p>
        </div>

        <div className="ocp-input-wrap">
          <input
            type="text"
            className="ocp-input"
            placeholder=""
            aria-label="Ask about your brand strategy"
          />
          <button type="button" className="ocp-send" aria-label="Send">
            ➤
          </button>
        </div>
      </main>

      <div className="ocp-orb" aria-hidden="true">
        <OrbPresence>
          <BrandOrb size="welcome" />
        </OrbPresence>
      </div>
    </div>
  );
}
