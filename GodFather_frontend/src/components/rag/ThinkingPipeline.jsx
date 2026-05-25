import "./ThinkingPipeline.css";

export default function ThinkingPipeline({ message, visible = true }) {
  if (!visible || !message) return null;

  return (
    <div className="thinking-pipeline" aria-live="polite">
      <span className="thinking-pipeline-dot" />
      <span className="thinking-pipeline-dot" />
      <span className="thinking-pipeline-dot" />
      <span className="thinking-pipeline-label">{message}</span>
    </div>
  );
}
