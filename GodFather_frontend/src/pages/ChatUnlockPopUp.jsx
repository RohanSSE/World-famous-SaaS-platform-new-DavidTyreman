import React from "react";
import { useNavigate } from "react-router-dom";
import "../components/ChatUnlockPopUp.css";
import unlockImage from "../assets/unlock-illustration.png";

export default function ChatUnlockPopUp() {
  const navigate = useNavigate();

  const handleUnlockNext = () => {
    // Navigate to ChatKickoffPage
    navigate("/ChatKickoffPage");
  };

  return (
    <div className="chat-unlock-bg">
      <div className="chat-unlock-card">
        <h1 className="chat-unlock-title">You're In!</h1>

        <div className="chat-unlock-illustration-wrapper">
          <img
            src={unlockImage}
            alt="Unlock illustration with clouds and padlock"
            className="chat-unlock-illustration"
          />
        </div>

        <p className="chat-unlock-subheading">
          "Let's Build Your World-Famous Brand."
        </p>

        <button className="chat-unlock-btn" onClick={handleUnlockNext}>
          Unlock Next Step
        </button>
      </div>
    </div>
  );
}