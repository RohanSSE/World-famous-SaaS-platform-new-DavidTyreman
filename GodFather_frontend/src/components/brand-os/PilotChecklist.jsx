import "./PilotChecklist.css";

const LABELS = {
  knowledge_uploaded: "Brand knowledge uploaded",
  onboarding_started: "Onboarding started",
  workflow_generated: "Workflow generated",
  export_downloaded: "Export downloaded",
  feedback_saved: "Feedback saved",
  learning_applied: "Learning applied",
};

export default function PilotChecklist({ checklist = {}, completionPct = 0 }) {
  const items = Object.entries(LABELS);
  if (!items.length) return null;

  return (
    <div className="pilot-checklist">
      <div className="pilot-checklist-header">
        <span>Pilot progress</span>
        <strong>{completionPct}%</strong>
      </div>
      <ul>
        {items.map(([key, label]) => (
          <li key={key} className={checklist[key] ? "done" : ""}>
            <span className="pilot-check-icon">{checklist[key] ? "✓" : "○"}</span>
            {label}
          </li>
        ))}
      </ul>
    </div>
  );
}
