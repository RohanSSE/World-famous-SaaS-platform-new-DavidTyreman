import { useNavigate, useLocation } from "react-router-dom";
import "./AgencyPendingPage.css";

export default function AgencyPendingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "";
  const message =
    location.state?.message ||
    "Your agency registration is pending. An administrator must approve your account before you can access the dashboard.";

  return (
    <div className="agency-pending-page">
      <div className="agency-pending-glow agency-pending-glow-1" />
      <div className="agency-pending-glow agency-pending-glow-2" />
      <div className="agency-pending-card">
        <div className="agency-pending-icon" aria-hidden>
          ⏳
        </div>
        <h1>Awaiting admin approval</h1>
        <p className="agency-pending-message">{message}</p>
        {email ? (
          <p className="agency-pending-email">
            Registered as <strong>{email}</strong>
          </p>
        ) : null}
        <ul className="agency-pending-steps">
          <li>Your agency has been submitted for review.</li>
          <li>An admin will activate your account from the admin panel.</li>
          <li>You can sign in again once approval is complete.</li>
        </ul>
        <div className="agency-pending-actions">
          <button type="button" className="agency-pending-btn primary" onClick={() => navigate("/login")}>
            Back to sign in
          </button>
          <button type="button" className="agency-pending-btn secondary" onClick={() => navigate("/intro-ductory")}>
            Go to home
          </button>
        </div>
      </div>
    </div>
  );
}
