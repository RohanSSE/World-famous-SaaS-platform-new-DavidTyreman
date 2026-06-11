import React, { useState, useEffect } from "react";
import "../components/Stepper.css";
import { useNavigate } from "react-router-dom";

/* ─── Step Data — easy to extend: just add an object to this array ─── */
const STEPS = [
  {
    id: 1,
    icon: "✦",
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
    label: "Create Account",
    tagline: "Secure your workspace",
    description:
      "Set up your account to save brand progress and access your workspace anytime.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
  {
    id: 2,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    label: "Start Session",
    tagline: "Begin your journey",
    description:
      "Launch a structured brand discovery session tailored to your business.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
  {
    id: 3,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    label: "Foundation Questions",
    tagline: "8 core questions",
    description:
      "Uncover your origin, beliefs, and positioning through 8 foundational brand questions.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
  {
    id: 4,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    label: "Brand Book",
    tagline: "Your first snapshot",
    description:
      "Generate your first strategic brand snapshot based on your foundational answers.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
  {
    id: 5,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
    label: "Brand Identity",
    tagline: "12 strategy questions",
    description:
      "Define your differentiation, audience, and brand promise with 12 required strategy questions.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
  {
    id: 6,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="11" y1="8" x2="11" y2="14" />
        <line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
    label: "Deep Dive",
    tagline: "Optional · 10 questions",
    description:
      "Add sharper positioning with 10 advanced optional questions for deeper brand clarity.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
    optional: true,
  },
  {
    id: 7,
    svgIcon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
    label: "Manifesto",
    tagline: "Brand Manifesto",
    description:
      "Your Brand Manifesto and full Brand Kit — beliefs, positioning, and complete identity.",
    color: "#3959E5",
    glowColor: "rgba(57, 89, 229, 0.35)",
  },
];

/* ─── Particle helper ─── */
function particleStyle(i) {
  const positions = [
    { top: "8%", left: "4%" },
    { top: "15%", left: "88%" },
    { top: "25%", left: "12%" },
    { top: "35%", left: "94%" },
    { top: "48%", left: "2%" },
    { top: "55%", left: "82%" },
    { top: "65%", left: "18%" },
    { top: "72%", left: "90%" },
    { top: "82%", left: "6%" },
    { top: "90%", left: "76%" },
    { top: "10%", left: "55%" },
    { top: "42%", left: "65%" },
    { top: "60%", left: "45%" },
    { top: "78%", left: "55%" },
    { top: "20%", left: "38%" },
    { top: "88%", left: "38%" },
    { top: "5%", left: "72%" },
    { top: "95%", left: "22%" },
  ];
  const p = positions[i] || { top: "50%", left: "50%" };
  const size = 2 + (i % 3);
  const delay = i * 0.7;
  const dur = 3 + (i % 4);
  return {
    position: "absolute",
    top: p.top,
    left: p.left,
    width: `${size}px`,
    height: `${size}px`,
    borderRadius: "50%",
    background:
      i % 3 === 0
        ? "#3959E5"
        : i % 3 === 1
          ? "#8ee5ff"
          : "rgba(255,255,255,0.5)",
    animation: `particleDrift ${dur}s ease-in-out ${delay}s infinite`,
    pointerEvents: "none",
  };
}

/* ─── Main Component ─── */
export default function Stepper({ onClose }) {
  const [activeStep, setActiveStep] = useState(null);
  const [hoveredStep, setHoveredStep] = useState(null);
  const [visibleSteps, setVisibleSteps] = useState([]);

  const navigate = useNavigate();

  /* Staggered reveal on mount */
  useEffect(() => {
    STEPS.forEach((_, i) => {
      setTimeout(() => {
        setVisibleSteps((prev) => [...prev, i]);
      }, 120 * i);
    });
  }, []);

  const displayed = hoveredStep !== null ? hoveredStep : activeStep;

  return (
    // <div
    //   className="bjm-overlay"
    //   onClick={(e) => {
    //     if (e.target === e.currentTarget && onClose) onClose();
    //   }}
    // >
    <div className="bjm-fullscreen">
      {/* Close button */}
      {/* {onClose && (
          <button className="bjm-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        )} */}

      {/* Background particles */}
      <div className="bjm-bg-particles">
        {[...Array(18)].map((_, i) => (
          <div key={i} style={particleStyle(i)} />
        ))}
      </div>

      {/* Header */}
      {/* <div className="bjm-header">
        <div className="bjm-header-badge">YOUR BRAND JOURNEY</div>
        <h1 className="bjm-heading">
          From Idea to
          <br />
          <span className="bjm-heading-accent">Unforgettable Brand</span>
        </h1>
        <p className="bjm-subheading">Seven steps. One powerful identity.</p>
      </div> */}
      <div className="bjm-header">
        <div className="bjm-header-side" />

        <div className="bjm-header-center">
          <div className="bjm-header-badge">YOUR BRAND JOURNEY</div>

          <h1 className="bjm-title">
            From Idea to <br />
            Unforgettable Brand
          </h1>
        </div>

        <div className="bjm-header-side right">
          <button
            className="bjm-continue-btn"
            onClick={() => navigate("/user-dashboard")}
          >
            Continue →
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="bjm-content">
        {/* ── Horizontal Steps Row ── */}
        <div className="bjm-steps-row">
          {STEPS.map((step, idx) => {
            const isVisible = visibleSteps.includes(idx);
            const isActive = activeStep === idx;
            const isHovered = hoveredStep === idx;
            const isHighlighted = isActive || isHovered;
            const isLastStep = idx === STEPS.length - 1;

            return (
              <div
                key={step.id}
                className="bjm-step-col"
                style={{
                  opacity: isVisible ? 1 : 0,
                  transform: isVisible ? "translateY(0)" : "translateY(20px)",
                  transition: `opacity 0.55s ease ${idx * 0.07}s, transform 0.55s cubic-bezier(0.34,1.2,0.64,1) ${idx * 0.07}s`,
                }}
                onClick={() => setActiveStep(isActive ? null : idx)}
                onMouseEnter={() => setHoveredStep(idx)}
                onMouseLeave={() => setHoveredStep(null)}
              >
                {/* Top: number badge + horizontal connector */}
                <div className="bjm-step-top">
                  {/* Number badge */}
                  <div
                    className="bjm-num-badge"
                    style={{
                      background: isHighlighted
                        ? `linear-gradient(135deg, ${step.color} 0%, ${step.color}cc 100%)`
                        : "rgb(2, 3, 51)",
                      border: isHighlighted
                        ? `1.5px solid ${step.color}`
                        : "1.5px solid rgba(255,255,255,0.1)",
                      boxShadow: isHighlighted
                        ? `0 0 18px ${step.glowColor}, 0 4px 12px rgba(0,0,0,0.4)`
                        : "none",
                      color: isHighlighted
                        ? "#fff"
                        : "rgba(255, 255, 255, 0.36)",
                    }}
                  >
                    {String(step.id).padStart(2, "0")}
                  </div>

                  {/* Horizontal connector line (not on last step) */}
                  {!isLastStep && (
                    <div className="bjm-connector-track-h">
                      <div
                        className="bjm-connector-fill-h"
                        style={{
                          width: isHighlighted ? "100%" : "0%",
                          background: `linear-gradient(to right, ${step.color}, ${STEPS[idx + 1]?.color || step.color})`,
                        }}
                      />
                    </div>
                  )}
                </div>

                {/* Icon */}
                <div
                  className="bjm-icon-wrap"
                  style={{
                    background: isHighlighted
                      ? `radial-gradient(circle at 35% 35%, ${step.color}44 0%, ${step.color}22 60%, transparent 100%)`
                      : "rgba(255,255,255,0.03)",
                    border: isHighlighted
                      ? `1.5px solid ${step.color}66`
                      : "1.5px solid rgba(255,255,255,0.07)",
                    boxShadow: isHighlighted
                      ? `0 0 24px ${step.glowColor}, inset 0 1px 0 rgba(255,255,255,0.1)`
                      : "inset 0 1px 0 rgba(255,255,255,0.04)",
                    transform: isHighlighted
                      ? "scale(1.08) rotate(-3deg)"
                      : "scale(1) rotate(0deg)",
                    color: isHighlighted ? step.color : "rgba(255,255,255,0.3)",
                  }}
                >
                  {step.svgIcon}
                </div>

                {/* Text */}
                <div className="bjm-step-text">
                  <div className="bjm-step-label-row">
                    <span
                      className="bjm-step-label"
                      style={{
                        color: isHighlighted ? "#fff" : "rgba(255,255,255,0.6)",
                      }}
                    >
                      {step.label}
                    </span>
                    {step.optional && (
                      <span className="bjm-optional-badge">Optional</span>
                    )}
                  </div>
                  <span
                    className="bjm-step-tagline"
                    style={{
                      color: isHighlighted
                        ? step.color
                        : "rgba(255,255,255,0.22)",
                    }}
                  >
                    {step.tagline}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Detail Panel ── */}
        <div className="bjm-detail-panel">
          {displayed !== null ? (
            <div
              key={displayed}
              className="bjm-detail-panel-inner"
              style={{
                borderColor: `${STEPS[displayed].color}33`,
                boxShadow: `0 0 60px ${STEPS[displayed].glowColor}, 0 20px 60px rgba(0,0,0,0.5)`,
                animation:
                  "panelFadeIn 0.4s cubic-bezier(0.4,0,0.2,1) forwards",
              }}
            >
              {/* Step number watermark */}
              {/* <div
                className="bjm-watermark-num"
                style={{ color: `${STEPS[displayed].color}18` }}
              >
                {String(STEPS[displayed].id).padStart(2, "0")}
              </div> */}

              {/* Top glow stripe */}
              <div
                className="bjm-panel-top-stripe"
                style={{
                  background: `linear-gradient(90deg, ${STEPS[displayed].color} 0%, ${STEPS[displayed].color}00 100%)`,
                }}
              />

              {/* Icon */}
              <div
                className="bjm-panel-icon"
                style={{
                  color: STEPS[displayed].color,
                  background: `radial-gradient(circle, ${STEPS[displayed].color}22 0%, transparent 70%)`,
                  border: `1.5px solid ${STEPS[displayed].color}44`,
                  boxShadow: `0 0 30px ${STEPS[displayed].glowColor}`,
                }}
              >
                {STEPS[displayed].svgIcon}
              </div>

              {/* Body text */}
              <div className="bjm-panel-body">
                <div className="bjm-panel-step-num">
                  STEP {STEPS[displayed].id} OF {STEPS.length}
                </div>
                <h2 className="bjm-panel-title">{STEPS[displayed].label}</h2>
                {/* <div
                  className="bjm-panel-tagline"
                  style={{ color: STEPS[displayed].color }}
                >
                  {STEPS[displayed].tagline}
                </div> */}
                <div className="bjm-panel-meta-row">
                  <div
                    className="bjm-panel-tagline"
                    style={{ color: STEPS[displayed].color }}
                  >
                    {STEPS[displayed].tagline}
                  </div>

                  {STEPS[displayed].optional && (
                    <div
                      className="bjm-panel-optional-inline"
                      style={{
                        borderColor: `${STEPS[displayed].color}44`,
                        color: STEPS[displayed].color,
                      }}
                    >
                      ✦ This step is optional — for brands that want deeper
                      clarity
                    </div>
                  )}
                </div>

                {/* Divider */}
                <div
                  className="bjm-panel-divider"
                  style={{
                    background: `linear-gradient(90deg, ${STEPS[displayed].color}55 0%, transparent 80%)`,
                  }}
                />

                <p className="bjm-panel-description">
                  {STEPS[displayed].description}
                </p>

                {/* {STEPS[displayed].optional && (
                  <div
                    className="bjm-panel-optional"
                    style={{
                      borderColor: `${STEPS[displayed].color}44`,
                      color: STEPS[displayed].color,
                    }}
                  >
                    ✦ This step is optional — for brands that want deeper
                    clarity
                  </div>
                )} */}
              </div>

              {/* Right: dots + nav */}
              <div className="bjm-panel-right">
                {/* Progress dots */}
                <div className="bjm-progress-dots">
                  {STEPS.map((s, i) => (
                    <div
                      key={i}
                      className="bjm-dot"
                      onClick={() => setActiveStep(i)}
                      style={{
                        background:
                          i === displayed
                            ? STEPS[displayed].color
                            : "rgba(255,255,255,0.12)",
                        width: i === displayed ? "24px" : "8px",
                        boxShadow:
                          i === displayed
                            ? `0 0 8px ${STEPS[displayed].glowColor}`
                            : "none",
                      }}
                    />
                  ))}
                </div>

                {/* Navigation arrows */}
                <div className="bjm-panel-nav">
                  <button
                    className="bjm-nav-btn"
                    onClick={() => setActiveStep(Math.max(0, displayed - 1))}
                    disabled={displayed === 0}
                    style={{
                      opacity: displayed === 0 ? 0.2 : 1,
                      borderColor: `${STEPS[displayed].color}55`,
                      color: STEPS[displayed].color,
                    }}
                  >
                    ←
                  </button>
                  <span className="bjm-nav-label">
                    {displayed + 1} / {STEPS.length}
                  </span>
                  <button
                    className="bjm-nav-btn"
                    onClick={() =>
                      setActiveStep(Math.min(STEPS.length - 1, displayed + 1))
                    }
                    disabled={displayed === STEPS.length - 1}
                    style={{
                      opacity: displayed === STEPS.length - 1 ? 0.2 : 1,
                      borderColor: `${STEPS[displayed].color}55`,
                      color: STEPS[displayed].color,
                    }}
                  >
                    →
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="bjm-detail-panel-empty">
              <div className="bjm-empty-icon">◈</div>
              <p className="bjm-empty-text">
                Hover or click any step
                <br />
                to explore details
              </p>
            </div>
          )}
        </div>
      </div>
      {/* </div> */}
    </div>
  );
}
