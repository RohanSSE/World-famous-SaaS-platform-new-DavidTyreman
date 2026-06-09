import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronDown, Key, LogOut, User } from "lucide-react";
import { toast } from "react-toastify";
import { useAuth } from "../../context/AuthProvider";
import ProfileModal from "../../pages/ProfileModal";
import ChangePasswordModal from "../../pages/ChangePasswordModal";
import "./OnboardingHeader.css";

export default function OnboardingHeader({ onLogoClick, phaseStatus }) {
  const navigate = useNavigate();
  const { auth, logout } = useAuth();
  const dropdownRef = useRef(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] = useState(false);

  const initials =
    auth.user?.name?.charAt(0)?.toUpperCase() ||
    auth.user?.email?.charAt(0)?.toUpperCase() ||
    "A";

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isDropdownOpen]);

  const handleLogout = async () => {
    setIsDropdownOpen(false);
    try {
      await logout();
      toast.success("Logged out successfully");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Logout failed");
    } finally {
      navigate("/intro-ductory", { replace: true });
    }
  };

  return (
    <header className="onboarding-header">
      <button
        type="button"
        className="onboarding-header-logo"
        onClick={() => (onLogoClick ? onLogoClick() : navigate("/welcome"))}
      >
        THE GODFATHER
      </button>
      {phaseStatus && (
        <div className="onboarding-phase-status" aria-label="Journey status">
          <div className="onboarding-phase-status-copy">
            <span className="onboarding-phase-status-title">{phaseStatus.title}</span>
            <span className="onboarding-phase-status-subtitle">{phaseStatus.subtitle}</span>
          </div>
          <div className="onboarding-phase-status-track" aria-hidden="true">
            <span
              className="onboarding-phase-status-fill"
              style={{ width: `${Math.max(0, Math.min(100, Number(phaseStatus.progress || 0)))}%` }}
            />
          </div>
        </div>
      )}
      <div className="onboarding-avatar-wrapper" ref={dropdownRef}>
        <button
          type="button"
          className="onboarding-header-avatar"
          title="Profile Options"
          aria-label="Profile options"
          aria-expanded={isDropdownOpen}
          onClick={() => setIsDropdownOpen((open) => !open)}
        >
          {auth.user?.profileImage ? (
            <img src={auth.user.profileImage} alt="Profile" className="onboarding-avatar-image" />
          ) : (
            initials
          )}
          <ChevronDown className={`onboarding-avatar-chevron ${isDropdownOpen ? "open" : ""}`} size={12} />
        </button>

        {isDropdownOpen && (
          <div className="onboarding-avatar-dropdown">
            <button
              type="button"
              className="onboarding-dropdown-item"
              onClick={() => {
                setIsDropdownOpen(false);
                setIsProfileModalOpen(true);
              }}
            >
              <User size={16} />
              <span>Edit Profile</span>
            </button>
            <button
              type="button"
              className="onboarding-dropdown-item"
              onClick={() => {
                setIsDropdownOpen(false);
                setIsChangePasswordModalOpen(true);
              }}
            >
              <Key size={16} />
              <span>Change Password</span>
            </button>
            <button type="button" className="onboarding-dropdown-item logout" onClick={handleLogout}>
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
      <ProfileModal isOpen={isProfileModalOpen} onClose={() => setIsProfileModalOpen(false)} />
      <ChangePasswordModal isOpen={isChangePasswordModalOpen} onClose={() => setIsChangePasswordModalOpen(false)} />
    </header>
  );
}
