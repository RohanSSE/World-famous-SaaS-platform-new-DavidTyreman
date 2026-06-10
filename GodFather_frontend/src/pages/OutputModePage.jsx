import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import "./OutputModePage.css";

const PILLS = [
  "Create Campaigns",
  "Strengthen Messaging",
  "Build Customer Trust",
  "Generate Community Engagement Ideas",
  "Develop Storytelling Concepts",
  "Create Thought Leadership",
  "Identify Strategic Opportunities",
  "Expand Your Brand Over Time",
];

export default function OutputModePage() {
  const navigate = useNavigate();

  return (
    <div className="omp-page">
      <header className="omp-topbar">
        <ChatNavbar
          showSaveButton={false}
          showDownloadButton={false}
          showLogoutButton
          phaseStatus={{
            title: "Output mode",
            subtitle: "Brand Book complete · Growth mode active",
            progress: 100,
          }}
        />
      </header>

      <main className="omp-main">
        <button type="button" className="omp-back" onClick={() => navigate("/brand-book-ready")}>
          Back
        </button>

        <h1>Welcome To Output Mode</h1>
        <p>
          Your Brand Book has now become the strategic intelligence layer behind your brand.
          From this point forward, the Brand Godfather can help you:
        </p>

        <div className="omp-pill-wrap">
          {PILLS.map((pill) => (
            <span key={pill} className="omp-pill">{pill}</span>
          ))}
        </div>

        <button type="button" className="omp-cta" onClick={() => navigate("/output-chat")}>
          Let&apos;s Grow Your Brand
        </button>
      </main>

      <div className="omp-orb" aria-hidden="true">
        <OrbPresence>
          <BrandOrb size="welcome" />
        </OrbPresence>
      </div>
    </div>
  );
}
