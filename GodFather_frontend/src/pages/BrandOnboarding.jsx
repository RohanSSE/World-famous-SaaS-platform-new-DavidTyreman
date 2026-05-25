import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import authService from "../services/authService";
import "./BrandOnboarding.css";

const STEPS = [
  {
    id: 1,
    title: "Upload brand context",
    body: "Add PDFs, website copy, founder notes, and competitor references to your session documents.",
    action: "Go to documents",
    path: "/user-dashboard",
  },
  {
    id: 2,
    title: "Generate strategic foundation",
    body: "Run Brand DNA, Positioning, Messaging, and Tone workflows in the Brand OS.",
    action: "Open Brand OS",
    path: "/brand-os",
  },
  {
    id: 3,
    title: "Refine with feedback learning",
    body: "Edit AI outputs, set preferred tone, and reject phrases — cognition adapts per session.",
    action: "Brand OS feedback",
    path: "/brand-os",
  },
  {
    id: 4,
    title: "Export deliverables",
    body: "Download agency-ready PDF brand book, messaging guide, or campaign PPTX.",
    action: "Export from Brand OS",
    path: "/brand-os",
  },
];

export default function BrandOnboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState(null);
  const current = STEPS[step - 1];

  useEffect(() => {
    const sid =
      localStorage.getItem("sessionId") ||
      JSON.parse(localStorage.getItem("session") || "{}")?.id;
    if (sid) setSessionId(String(sid));
  }, []);

  const trackStep = (stepId) => {
    if (!sessionId) return;
    authService
      .recordPilotEvent(sessionId, "onboarding_step", { step: stepId })
      .catch(() => {});
  };

  return (
    <div className="brand-onboarding">
      <header>
        <h1>Brand cognition onboarding</h1>
        <p>Four steps from documents → strategy → refinement → deliverables</p>
      </header>

      <div className="onboarding-progress">
        {STEPS.map((s) => (
          <button
            key={s.id}
            type="button"
            className={step === s.id ? "active" : step > s.id ? "done" : ""}
            onClick={() => {
              setStep(s.id);
              trackStep(s.id);
            }}
          >
            {s.id}
          </button>
        ))}
      </div>

      <article className="onboarding-card">
        <h2>
          Step {current.id}: {current.title}
        </h2>
        <p>{current.body}</p>
        <button
          type="button"
          className="onboarding-primary"
          onClick={() => {
            trackStep(current.id);
            navigate(current.path);
            toast.info(current.action);
          }}
        >
          {current.action}
        </button>
      </article>

      <footer className="onboarding-footer">
        <button type="button" disabled={step <= 1} onClick={() => setStep((s) => s - 1)}>
          Back
        </button>
        {step < 4 ? (
          <button type="button" onClick={() => setStep((s) => s + 1)}>
            Next
          </button>
        ) : (
          <button type="button" className="onboarding-primary" onClick={() => navigate("/brand-os")}>
            Finish — open Brand OS
          </button>
        )}
      </footer>
    </div>
  );
}
