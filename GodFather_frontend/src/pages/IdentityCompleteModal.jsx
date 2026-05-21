// import React, { useEffect, useRef, useState } from "react";
// import "../components/Identitycompletemodal.css";

// export default function IdentityCompleteModal({ isOpen, onClose, onDeepDive }) {
//   const [visible, setVisible] = useState(false);
//   const [animIn, setAnimIn] = useState(false);
//   const overlayRef = useRef(null);

//   useEffect(() => {
//     if (isOpen) {
//       setVisible(true);
//       // slight delay so CSS transition triggers
//       requestAnimationFrame(() => {
//         requestAnimationFrame(() => setAnimIn(true));
//       });
//     } else {
//       setAnimIn(false);
//       const t = setTimeout(() => setVisible(false), 400);
//       return () => clearTimeout(t);
//     }
//   }, [isOpen]);

//   function handleClose() {
//     setAnimIn(false);
//     setTimeout(() => {
//       setVisible(false);
//       onClose();
//     }, 350);
//   }

//   function handleDeepDive() {
//     setAnimIn(false);
//     setTimeout(() => {
//       setVisible(false);
//       onDeepDive();
//     }, 300);
//   }

//   if (!visible) return null;

//   return (
//     <div
//       className={`icm-overlay ${animIn ? "icm-overlay--in" : ""}`}
//       ref={overlayRef}
//       onClick={(e) => {
//         if (e.target === overlayRef.current) handleClose();
//       }}
//     >
//       <div className={`icm-card ${animIn ? "icm-card--in" : ""}`}>
//         {/* Decorative top band */}
//         <div className="icm-band" />

//         {/* Close button */}
//         <button className="icm-close-btn" onClick={handleClose} aria-label="Close">
//           <span>✕</span>
//         </button>

//         {/* Trophy / badge area */}
//         <div className="icm-badge-wrap">
//           <div className="icm-badge-ring icm-badge-ring--outer" />
//           <div className="icm-badge-ring icm-badge-ring--mid" />
//           <div className="icm-badge-ring icm-badge-ring--inner" />
//           <div className="icm-badge-icon">🏆</div>
//         </div>

//         {/* Headline */}
//         <div className="icm-headline-wrap">
//           <p className="icm-eyebrow">Stage Complete</p>
//           <h2 className="icm-headline">
//             Identity&nbsp;
//             <span className="icm-headline-accent">Unlocked.</span>
//           </h2>
//           <p className="icm-body">
//             You've answered every question in the&nbsp;
//             <strong>Brand Identity</strong> stage. Your brand now has a
//             heartbeat — a direction, a voice, and a reason to exist.
//           </p>
//           <p className="icm-body icm-body--sub">
//             Want to go deeper? The <em>Deep Dive</em> unlocks 10 optional
//             questions that sharpen your brand's edge — audience precision,
//             visual language, anti-positioning, and more.
//           </p>
//         </div>

//         {/* Stats strip */}
//         <div className="icm-stats">
//           <div className="icm-stat">
//             <span className="icm-stat-num">3</span>
//             <span className="icm-stat-label">Categories</span>
//           </div>
//           <div className="icm-stat-divider" />
//           <div className="icm-stat">
//             <span className="icm-stat-num">12</span>
//             <span className="icm-stat-label">Questions Answered</span>
//           </div>
//           <div className="icm-stat-divider" />
//           <div className="icm-stat">
//             <span className="icm-stat-num">10</span>
//             <span className="icm-stat-label">Optional Awaiting</span>
//           </div>
//         </div>

//         {/* CTA buttons */}
//         <div className="icm-actions">
//           <button className="icm-btn icm-btn--skip" onClick={handleClose}>
//             <span className="icm-btn-icon">→</span>
//             Skip for now
//           </button>
//           <button className="icm-btn icm-btn--deepdive" onClick={handleDeepDive}>
//             <span className="icm-btn-glow" />
//             <span className="icm-btn-icon">✦</span>
//             Deep Dive
//             <span className="icm-btn-sub">10 optional questions</span>
//           </button>
//         </div>

//         {/* Floating particles */}
//         <div className="icm-particles" aria-hidden="true">
//           {[...Array(12)].map((_, i) => (
//             <span key={i} className={`icm-particle icm-particle--${i + 1}`} />
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }

// import React, { useEffect, useRef, useState } from "react";
// import "../components/Identitycompletemodal.css";

// export default function IdentityCompleteModal({ isOpen, onClose, onDeepDive }) {
//   const [visible, setVisible] = useState(false);
//   const [animIn, setAnimIn]   = useState(false);
//   const overlayRef            = useRef(null);

//   useEffect(() => {
//     if (isOpen) {
//       setVisible(true);
//       requestAnimationFrame(() => requestAnimationFrame(() => setAnimIn(true)));
//     } else {
//       setAnimIn(false);
//       const t = setTimeout(() => setVisible(false), 400);
//       return () => clearTimeout(t);
//     }
//   }, [isOpen]);

//   function handleClose() {
//     setAnimIn(false);
//     setTimeout(() => { setVisible(false); onClose(); }, 350);
//   }
//   function handleDeepDive() {
//     setAnimIn(false);
//     setTimeout(() => { setVisible(false); onDeepDive(); }, 300);
//   }

//   if (!visible) return null;

//   return (
//     <div
//       className={`icm-overlay ${animIn ? "icm-overlay--in" : ""}`}
//       ref={overlayRef}
//       onClick={(e) => { if (e.target === overlayRef.current) handleClose(); }}
//     >
//       <div className={`icm-card ${animIn ? "icm-card--in" : ""}`}>
//         <div className="icm-band" />
//         <button className="icm-close-btn" onClick={handleClose} aria-label="Close">✕</button>

//         <div className="icm-badge-wrap">
//           <div className="icm-badge-ring icm-badge-ring--outer" />
//           <div className="icm-badge-ring icm-badge-ring--mid" />
//           <div className="icm-badge-ring icm-badge-ring--inner" />
//           <div className="icm-badge-icon">🏆</div>
//         </div>

//         <div className="icm-headline-wrap">
//           <p className="icm-eyebrow">Stage Complete</p>
//           <h2 className="icm-headline">
//             Identity <span className="icm-headline-accent">Unlocked.</span>
//           </h2>
//           <p className="icm-body">
//             You've answered every question in the <strong>Brand Identity</strong> stage.
//             Your brand now has a heartbeat — a direction, a voice, and a reason to exist.
//           </p>
//           <p className="icm-body icm-body--sub">
//             Want to go deeper? The <em>Deep Dive</em> unlocks 10 optional questions
//             that sharpen your brand's edge — audience precision, visual language,
//             anti-positioning, and more.
//           </p>
//         </div>

//         <div className="icm-stats">
//           <div className="icm-stat">
//             <span className="icm-stat-num">3</span>
//             <span className="icm-stat-label">Categories</span>
//           </div>
//           <div className="icm-stat-divider" />
//           <div className="icm-stat">
//             <span className="icm-stat-num">12</span>
//             <span className="icm-stat-label">Answered</span>
//           </div>
//           <div className="icm-stat-divider" />
//           <div className="icm-stat">
//             <span className="icm-stat-num">10</span>
//             <span className="icm-stat-label">Optional</span>
//           </div>
//         </div>

//         <div className="icm-actions">
//           <button className="icm-btn icm-btn--skip" onClick={handleClose}>
//             <span className="icm-btn-icon">→</span>
//             Skip for now
//           </button>
//           <button className="icm-btn icm-btn--deepdive" onClick={handleDeepDive}>
//             <span className="icm-btn-glow" />
//             <span className="icm-btn-icon">✦</span>
//             Deep Dive
//             <span className="icm-btn-sub">10 optional questions</span>
//           </button>
//         </div>

//         <div className="icm-particles" aria-hidden="true">
//           {[...Array(12)].map((_, i) => (
//             <span key={i} className={`icm-particle icm-particle--${i + 1}`} />
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }

//16/02/2026
import React, { useEffect, useRef, useState } from "react";
import "../components/Identitycompletemodal.css";
import { useNavigate } from "react-router-dom";

export default function IdentityCompleteModal({ isOpen, onClose, onDeepDive, onManifesto }) {
  const [visible, setVisible] = useState(false);
  const [animIn, setAnimIn] = useState(false);
  const overlayRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isOpen) {
      setVisible(true);
      requestAnimationFrame(() => {
        requestAnimationFrame(() => setAnimIn(true));
      });
    } else {
      setAnimIn(false);
      const t = setTimeout(() => setVisible(false), 400);
      return () => clearTimeout(t);
    }
  }, [isOpen]);

  function handleClose() {
    setAnimIn(false);
    setTimeout(() => {
      setVisible(false);
      onClose?.();
    }, 350);
  }

  function handleDeepDive() {
    setAnimIn(false);
    setTimeout(() => {
      setVisible(false);
      onDeepDive?.();
    }, 280);
  }

  function handleManifesto() {
    setAnimIn(false);
    setTimeout(() => {
      setVisible(false);
      onManifesto?.();
    }, 280);
  }

  return (
    <>
      {visible && (
        <div
          className={`icm-overlay ${animIn ? "icm-overlay--in" : ""}`}
          ref={overlayRef}
          onClick={(e) => {
            if (e.target === overlayRef.current) handleClose();
          }}
        >
          <div className={`icm-card ${animIn ? "icm-card--in" : ""}`}>

            {/* Animated top band */}
            <div className="icm-band" />

            {/* Close */}
            <button className="icm-close-btn" onClick={handleClose} aria-label="Close">✕</button>

            {/* Trophy badge */}
            <div className="icm-badge-wrap">
              <div className="icm-badge-ring icm-badge-ring--outer" />
              <div className="icm-badge-ring icm-badge-ring--mid" />
              <div className="icm-badge-ring icm-badge-ring--inner" />
              <div className="icm-badge-icon">🏆</div>
            </div>

            {/* Headline */}
            <div className="icm-headline-wrap">
              {/* <p className="icm-eyebrow">Stage Complete</p> */}
              <h2 className="icm-headline">
                Stage&nbsp;<span className="icm-headline-accent">Complete</span>
              </h2>
              {/* <p className="icm-body">
                You've answered every question in the&nbsp;
                <strong>Brand Identity</strong> stage. Your brand now has
                a heartbeat — a direction, a voice, and a reason to exist.
              </p> */}
              <p className="icm-body icm-body--sub">
                Want to go deeper? The&nbsp;<em>Deep Dive</em>&nbsp;unlocks 10 optional
                questions that sharpen your brand's edge even more.
              </p>
            </div>

            {/* Stats strip */}
            {/* <div className="icm-stats">
              <div className="icm-stat">
                <span className="icm-stat-num">3</span>
                <span className="icm-stat-label">Categories</span>
              </div>
              <div className="icm-stat-divider" />
              <div className="icm-stat">
                <span className="icm-stat-num">12</span>
                <span className="icm-stat-label">Questions Answered</span>
              </div>
              <div className="icm-stat-divider" />
              <div className="icm-stat">
                <span className="icm-stat-num">10</span>
                <span className="icm-stat-label">Optional Awaiting</span>
              </div>
            </div> */}

            {/* CTA buttons */}
            <div className="icm-actions">
              <button className="icm-btn icm-btn--skip" onClick={handleClose}>
                Skip for now
              </button>
              <button className="icm-btn icm-btn--deepdive" onClick={handleDeepDive}>
                <span className="icm-btn-glow" />
                Deep Dive
              </button>
              <button className="icm-btn icm-btn--manifesto" onClick={handleManifesto}>
                <span className="icm-btn-glow" />
                My Manifesto
              </button>
            </div>

            {/* Floating particles */}
            <div className="icm-particles" aria-hidden="true">
              {[...Array(12)].map((_, i) => (
                <span key={i} className={`icm-particle icm-particle--${i + 1}`} />
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}