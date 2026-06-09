import React, { useState , useEffect, useRef} from "react";
import "../components/IntroductoryPage.css";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthProvider";
import { toast } from "react-toastify";
import PageTransition from "../context/PageTransition";
import bg from "../assets/Rectangle.jpg";
import logo from "../assets/mask-group.png";

import videoBg from "../assets/GettyImages.mov";
import ChatNavbar from "./ChatNavbar";
import SignupLoginModal from "./SignupLoginModal";
const INTRO_CORNER_VIDEO =
  "/magnific_i-want-to-remove-the-background-of-this-video-and-_auto_720p_24fps_96756.mp4";



export default function IntroductoryPage() {
  const navigate = useNavigate();
  const { logout, auth } = useAuth();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState("signup");
  const [showVideoPopup, setShowVideoPopup] = useState(true); // Show popup by default
  const [showFullscreenVideo, setShowFullscreenVideo] = useState(false);

  const videoRef = useRef();
  const youtubeVideoId = "xeXV1KoX034"; // Extracted from the YouTube URL

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = 0.5; // 0.5 = half speed, adjust as needed
    }
  }, []);

const handleCtaClick = () => {
  if (auth.isAuthenticated && auth.user) {
    // Check if user is agency by numeric role id
    const isAgency = auth.user?.role === 3;

    if (isAgency) {
      navigate("/agency-dashboard");
    } else if (localStorage.getItem("sessionId")) {
      navigate("/phase-questions/1");
    } else {
      navigate("/welcome");
    }
  } else {
    setModalMode("signup");
    setIsModalOpen(true);
  }
};



  const handleLoginClick = () => {
    setModalMode("login");
    setIsModalOpen(true);           
  };

  const handleSignupClick = () => {
    setModalMode("signup");
    setIsModalOpen(true);
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

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleVideoPlay = () => {
    setShowFullscreenVideo(true);
    setShowVideoPopup(false);
  };

  const closeFullscreenVideo = () => {
    setShowFullscreenVideo(false);
  };

  const closeVideoPopup = () => {
    setShowVideoPopup(false);
  };

  return (
    <>
      <PageTransition>
        <div className="intro-page">
          {/* Background */}
          <video
            className="intro-bg-video"
            src={videoBg}
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            aria-hidden="true"
          />

          {/* Background image fallback (keep or remove as you like) */}
          {/* <div
          className="intro-bg"
          style={{ backgroundImage: `url(${bg})` }}
          aria-hidden="true"
        ></div> */}

          {/* Header */}
          {/* Conditionally render Navbar or login/signup buttons */}
          {auth.isAuthenticated && auth.user ? (
            <ChatNavbar 
              showDownloadButton={false} // optional adjustments
              showSaveButton={false}
              showLogoutButton={true}
              phaseStatus={{
                title: "Brand journey",
                subtitle: "Ready to continue",
                progress: localStorage.getItem("sessionId") ? 25 : 5,
              }}
            />
          ) : (
            <header className="intro-header">
              <div className="intro-logo">
                <img src={logo} alt="The Brand Godfather logo" />
              </div>
              <div className="intro-buttons">
                <button className="btn-outline" onClick={handleLoginClick}>
                  Log in
                </button>
                <button className="btn-solid" onClick={handleSignupClick}>
                  Sign up
                </button>
              </div>
            </header>
          )}

          {/* Horizontal Divider Line */}
          <div className="intro-divider" aria-hidden="true"></div>

          {/* Tagline - Just below the line */}
          <div className="intro-tagline-section">
            <p className="intro-tagline">
              DISCOVER YOUR STORY, YOUR VOICE, AND YOUR DIFFERENCE — ALL IN ONE
              PLACE
            </p>
          </div>

          {/* Main content - Centered (Title + CTA) */}
          <main className="intro-content">
            <h1 className="intro-title">DEFINE YOUR BRAND</h1>
            <button className="intro-cta" onClick={handleCtaClick}>
              {auth.isAuthenticated
                ? "Continue Your Brand Journey"
                : "Start Your Brand Journey"}
            </button>
          </main>
        </div>

        {/* Signup/Login Modal */}
        <SignupLoginModal
          isOpen={isModalOpen}
          onClose={closeModal}
          initialMode={modalMode}
        />

        {/* Bottom-right — magnific video only (no ring combo) */}
        <div className="intro-corner-video" aria-hidden="true">
          <div className="intro-corner-video__clip">
            <video
              className="intro-corner-video__el"
              src={INTRO_CORNER_VIDEO}
              autoPlay
              loop
              muted
              playsInline
              preload="auto"
            />
          </div>
        </div>

        {/* Video Popup - bottom-left (compact) */}
        {showVideoPopup && (
          <div className="video-popup-overlay video-popup-overlay--left" onClick={closeVideoPopup}>
            <div className="video-popup video-popup--compact" onClick={(e) => e.stopPropagation()}>
              <button className="video-popup-close" onClick={closeVideoPopup}>
                ×
              </button>
              <div className="video-popup-content">
                <h3 className="video-popup-title">Watch Our Story</h3>
                <div className="video-popup-preview" onClick={handleVideoPlay}>
                  <img
                    src={`https://img.youtube.com/vi/${youtubeVideoId}/maxresdefault.jpg`}
                    alt="Video thumbnail"
                    className="video-thumbnail"
                  />
                  <div className="video-play-button">
                    <svg
                      width="56"
                      height="56"
                      viewBox="0 0 80 80"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <circle cx="40" cy="40" r="40" fill="rgba(0,0,0,0.6)" />
                      <path
                        d="M32 24L56 40L32 56V24Z"
                        fill="white"
                      />
                    </svg>
                  </div>
                </div>
                <p className="video-popup-description">
                  Click to watch our brand story in fullscreen
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Fullscreen Video Modal */}
        {showFullscreenVideo && (
          <div className="fullscreen-video-overlay" onClick={closeFullscreenVideo}>
            <div className="fullscreen-video-container" onClick={(e) => e.stopPropagation()}>
              <button className="fullscreen-video-close" onClick={closeFullscreenVideo}>
                ×
              </button>
              <div className="fullscreen-video-wrapper">
                <iframe
                  className="fullscreen-video-iframe"
                  src={`https://www.youtube.com/embed/${youtubeVideoId}?autoplay=1&rel=0`}
                  title="YouTube video player"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            </div>
          </div>
        )}
      </PageTransition>
    </>
  );
}
