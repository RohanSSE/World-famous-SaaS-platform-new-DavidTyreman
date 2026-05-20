// src/components/ChatUnlockModal.jsx
import React, { useEffect, useRef } from "react";
import ReactDOM from "react-dom";
import { useNavigate } from "react-router-dom";
import unlockBg from "../assets/Unlock-chat.png";
import "./ChatUnlockPopUp.css";

export default function ChatUnlockModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  const modalRef = useRef(null);
  const prevActive = useRef(null);

  useEffect(() => {
    prevActive.current = document.activeElement;
    const fqsApp = document.querySelector(".fqs-app");

    if (isOpen) {
      document.body.style.overflow = "hidden";
      document.body.classList.add("cun-modal-open");
      if (fqsApp) fqsApp.classList.add("cun-modal-open");
      setTimeout(() => modalRef.current?.focus?.(), 20);
    } else {
      document.body.style.overflow = "";
      document.body.classList.remove("cun-modal-open");
      if (fqsApp) fqsApp.classList.remove("cun-modal-open");
      try { prevActive.current?.focus(); } catch {}
    }

    const onKey = (e) => {
      if (!isOpen) return;
      if (e.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      document.body.classList.remove("cun-modal-open");
      if (fqsApp) fqsApp.classList.remove("cun-modal-open");
      document.removeEventListener("keydown", onKey);
      try { prevActive.current?.focus(); } catch {}
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div
      className="cun-overlay"
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose?.();
      }}
    >
      <div
        className="cun-image-card"
        ref={modalRef}
        tabIndex={-1}
        aria-labelledby="cun-title"
        style={{ backgroundImage: `url(${unlockBg})` }}
      >
        {/* overlay content placed inside the image area */}
        <h2 id="cun-title" className="cun-image-title">You're In!</h2>

        <p className="cun-image-sub">“Let's Build Your World-Famous Brand.”</p>

        <button
          className="cun-image-cta"
          onClick={() => navigate("/ChatKickoffPage")}
        >
          Unlock Next Step
        </button>
      </div>
    </div>,
    document.body
  );
}
