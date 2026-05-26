import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthProvider";
import "./OnboardingHeader.css";

export default function OnboardingHeader({ onLogoClick }) {
  const navigate = useNavigate();
  const { auth } = useAuth();

  const initials =
    auth.user?.name?.charAt(0)?.toUpperCase() ||
    auth.user?.email?.charAt(0)?.toUpperCase() ||
    "A";

  return (
    <header className="onboarding-header">
      <button
        type="button"
        className="onboarding-header-logo"
        onClick={() => (onLogoClick ? onLogoClick() : navigate("/welcome"))}
      >
        THE GODFATHER
      </button>
      <div className="onboarding-header-avatar" title="Account">
        {initials}
      </div>
    </header>
  );
}
