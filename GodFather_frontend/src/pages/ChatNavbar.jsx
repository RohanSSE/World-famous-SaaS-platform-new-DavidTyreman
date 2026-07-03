// import React, { useState, useRef, useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import { useAuth } from "../context/AuthProvider";
// import { toast } from "react-toastify";
// import { Download, LogOut, User, ChevronDown } from "lucide-react";

// import "../components/ChatNavbar.css";
// import logo from "../assets/mask-group.png";
// import ProfileModal from "./ProfileModal";

// const ChatNavbar = ({
//   sessionId,
//   onSave,
//   onDownloadPdf,
//   showSaveButton = true,
//   showDownloadButton = true,
//   showLogoutButton = true,
//   showCommentButton = false, // Add this default prop
//   onCommentClick = null,
// }) => {
//   const navigate = useNavigate();
//   const { logout, auth } = useAuth();
//   const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
//   const [isDropdownOpen, setIsDropdownOpen] = useState(false);
//   const dropdownRef = useRef(null);

//   const handleSave = () => {
//     if (onSave) {
//       onSave();
//     } else {
//       toast.success("Saved successfully!");
//       console.log("Save functionality");
//     }
//   };

//   const handleDownloadPdf = () => {
//     if (onDownloadPdf) {
//       onDownloadPdf();
//     } else {
//       toast.info("PDF download starting...");
//       console.log("Download PDF functionality");
//     }
//   };

//   const handleLogout = async () => {
//     try {
//       await logout();
//       toast.success("Logged out successfully");
//       navigate("/"); // Navigate to IntroductoryPage
//     } catch (error) {
//       console.error("Logout error:", error);
//       toast.error("Logout failed");
//       navigate("/"); // Still navigate
//     }
//   };

//   const handleEditProfile = () => {
//     setIsDropdownOpen(false);
//     setIsProfileModalOpen(true);
//   };

//   const toggleDropdown = () => {
//     setIsDropdownOpen(!isDropdownOpen);
//   };

//   const getInitials = () => {
//     if (auth.user?.name) {
//       return auth.user.name.charAt(0).toUpperCase();
//     }
//     if (auth.user?.email) {
//       return auth.user.email.charAt(0).toUpperCase();
//     }
//     return "A";
//   };

//   // Close dropdown when clicking outside
//   useEffect(() => {
//     const handleClickOutside = (event) => {
//       if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
//         setIsDropdownOpen(false);
//       }
//     };

//     if (isDropdownOpen) {
//       document.addEventListener("mousedown", handleClickOutside);
//     }

//     return () => {
//       document.removeEventListener("mousedown", handleClickOutside);
//     };
//   }, [isDropdownOpen]);

//   return (
//     <>
//       <header className="chat-header">
//         <div
//           className="chat-logo-wrap"
//           onClick={() => navigate("/intro-ductory")}
//         >
//           <img src={logo} alt="The Godfather" className="chat-logo" />
//         </div>

//         <div className="chat-header-actions">
//           {auth.user?.role === 2 && showSaveButton && (
//             <button className="btn-white" onClick={handleSave}>
//               Generate
//             </button>
//           )}

//           {auth.user?.role === 3 && showCommentButton && onCommentClick && (
//             <button className="btn-white" onClick={onCommentClick}>
//               Add Comment
//             </button>
//           )}

//           {showDownloadButton && (
//             <button className="btn-gradient" onClick={handleDownloadPdf}>
//               <Download className="download-icon" />
//               <span>Download PDF</span>
//             </button>
//           )}

//           {/* Avatar with Dropdown */}
//           <div className="avatar-dropdown-wrapper" ref={dropdownRef}>
//             <div
//               className="chat-avatar"
//               onClick={toggleDropdown}
//               title="Profile Options"
//             >
//               {auth.user?.profileImage ? (
//                 <img
//                   src={auth.user.profileImage}
//                   alt="Profile"
//                   className="avatar-image"
//                 />
//               ) : (
//                 getInitials()
//               )}
//               <ChevronDown
//                 className={`avatar-chevron ${isDropdownOpen ? "open" : ""}`}
//                 size={14}
//               />
//             </div>

//             {/* Dropdown Menu */}
//             {isDropdownOpen && (
//               <div className="avatar-dropdown">
//                 <button className="dropdown-item" onClick={handleEditProfile}>
//                   <User size={16} />
//                   <span>Edit Profile</span>
//                 </button>
//                 {showLogoutButton && (
//                   <button
//                     className="dropdown-item logout-item"
//                     onClick={handleLogout}
//                   >
//                     <LogOut size={16} />
//                     <span>Logout</span>
//                   </button>
//                 )}
//               </div>
//             )}
//           </div>
//         </div>
//       </header>

//       {/* Profile Modal */}
//       <ProfileModal
//         isOpen={isProfileModalOpen}
//         onClose={() => setIsProfileModalOpen(false)}
//       />
//     </>
//   );
// };

// export default ChatNavbar;

import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthProvider";
import { toast } from "react-toastify";
import { Download, LogOut, User, ChevronDown, Key, Bell } from "lucide-react";

import "../components/ChatNavbar.css";
import logo from "../assets/mask-group.png";
import ProfileModal from "./ProfileModal";
import ChangePasswordModal from "./ChangePasswordModal";

const ChatNavbar = ({
  sessionId,
  onSave,
  onGenerate, // function passed from page
  onDownloadPdf,
  downloadLabel = "Download PDF",
  downloadDisabled = false,
  showSaveButton = true,
  saveButtonLabel = "Save",
  saveButtonSavingLabel = "Saving...",
  saveButtonTitle,
  saveButtonDisabledTitle = "Complete all 30 questions to save",
  showDownloadButton = true,
  showLogoutButton = true,
  showCommentButton = false,
  showNotificationButton = false,
  onCommentClick = null,
  onNotificationClick = null,
  canGenerate = false,
  saveDisabled = false,
  phaseStatus = null,
  leadingAction = null,
}) => {
  const navigate = useNavigate();
  const { logout, auth } = useAuth();
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] =
    useState(false);

  const handleSave = async () => {
    if (saving || saveDisabled) return;
    if (onSave) {
      try {
        setSaving(true);
        await onSave();
      } catch (err) {
        console.error("Save failed:", err);
        toast.error(err?.message || "Failed to save");
      } finally {
        setSaving(false);
      }
    } else {
      toast.success("Saved successfully!");
      console.log("Save functionality");
    }
  };

  const handleDownloadPdf = () => {
    if (onDownloadPdf) {
      onDownloadPdf();
    } else {
      toast.info("PDF download starting...");
      console.log("Download PDF functionality");
    }
  };

  const handleGenerateClick = async () => {
    if (generating) return;
    if (onGenerate) {
      try {
        setGenerating(true);
        await onGenerate();
      } catch (err) {
        console.error("Generate failed:", err);
        toast.error(err?.message || "Failed to generate manifesto");
      } finally {
        setGenerating(false);
      }
      return;
    }

    toast.info("Generate requested (no handler provided).");
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Logged out successfully");
      navigate("/intro-ductory", { replace: true });
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Logout failed");
      navigate("/intro-ductory", { replace: true });
    }
  };

  const handleEditProfile = () => {
    setIsDropdownOpen(false);
    setIsProfileModalOpen(true);
  };

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const getInitials = () => {
    if (auth.user?.name) {
      return auth.user.name.charAt(0).toUpperCase();
    }
    if (auth.user?.email) {
      return auth.user.email.charAt(0).toUpperCase();
    }
    return "A";
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  return (
    <>
      <header className="chat-header">
        {leadingAction && <div className="chat-leading-action">{leadingAction}</div>}
        <div
          className="chat-logo-wrap"
          onClick={() => navigate("/intro-ductory")}
        >
          <img src={logo} alt="The Godfather" className="chat-logo" />
        </div>

        {phaseStatus && (
          <div className="chat-phase-status" aria-label="Phase progress">
            <div className="chat-phase-status-copy">
              <span className="chat-phase-status-title">{phaseStatus.title}</span>
              <span className="chat-phase-status-subtitle">{phaseStatus.subtitle}</span>
            </div>
            <div className="chat-phase-status-track" aria-hidden="true">
              <span
                className="chat-phase-status-fill"
                style={{ width: `${Math.max(0, Math.min(100, Number(phaseStatus.progress || 0)))}%` }}
              />
            </div>
          </div>
        )}

        <div className="chat-header-actions">
          {/* ✅ SAVE BUTTON – calls onSave from parent */}
          {showSaveButton && (
            <button 
              className="btn-white" 
              onClick={handleSave}
              disabled={saving || saveDisabled}
              title={saveDisabled ? saveButtonDisabledTitle : saveButtonTitle}
            >
              {saving ? (
                <>
                  <span className="spinner"></span>
                  <span>{saveButtonSavingLabel}</span>
                </>
              ) : (
                saveButtonLabel
              )}
            </button>
          )}
          
          {auth.user?.role === 2 && showSaveButton && canGenerate && (
            <button
              className="btn-white"
              onClick={handleGenerateClick}
              disabled={generating}
            >
              {generating ? "Generating..." : "Generate"}
            </button>
          )}

          {auth.user?.role === 3 && showCommentButton && onCommentClick && (
            <button className="btn-white" onClick={onCommentClick}>
              Add Comment
            </button>
          )}

          {showDownloadButton && (
            <button className="btn-gradient" onClick={handleDownloadPdf} disabled={downloadDisabled}>
              <Download className="download-icon" />
              <span>{downloadLabel}</span>
            </button>
          )}

          {showNotificationButton && (
            <button
              type="button"
              className="chat-icon-btn"
              onClick={onNotificationClick}
              aria-label="Notifications"
              title="Notifications"
            >
              <Bell size={18} />
            </button>
          )}

          <div className="avatar-dropdown-wrapper" ref={dropdownRef}>
            <div
              className="chat-avatar"
              onClick={toggleDropdown}
              title="Profile Options"
            >
              {auth.user?.profileImage ? (
                <img
                  src={auth.user.profileImage}
                  alt="Profile"
                  className="avatar-image"
                />
              ) : (
                getInitials()
              )}
              <ChevronDown
                className={`avatar-chevron ${isDropdownOpen ? "open" : ""}`}
                size={14}
              />
            </div>

            {isDropdownOpen && (
              <div className="avatar-dropdown">
                <button className="dropdown-item" onClick={handleEditProfile}>
                  <User size={16} />
                  <span>Edit Profile</span>
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => {
                    setIsDropdownOpen(false);
                    setIsChangePasswordModalOpen(true); // <- open password modal
                  }}
                >
                  <Key size={16} />
                  <span style={{ marginLeft: "8px" }}>Change Password</span>
                </button>
                {showLogoutButton && (
                  <button
                    className="dropdown-item logout-item"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    <span>Logout</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </header>
      <ChangePasswordModal
        isOpen={isChangePasswordModalOpen}
        onClose={() => setIsChangePasswordModalOpen(false)}
      />

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
      />
    </>
  );
};

export default ChatNavbar;
