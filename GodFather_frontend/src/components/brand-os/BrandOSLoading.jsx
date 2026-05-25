import "./BrandOSLoading.css";

const STAGES = [
  "Retrieving brand evidence",
  "Grounding strategic claims",
  "Applying brand cognition",
  "Verifying consistency",
];

export default function BrandOSLoading({ stage = 0, visible = false }) {
  if (!visible) return null;
  const label = STAGES[Math.min(stage, STAGES.length - 1)];

  return (
    <div className="brand-os-loader" role="status" aria-live="polite">
      <div className="brand-os-loader-ring" />
      <p className="brand-os-loader-title">Strategic cognition in progress</p>
      <p className="brand-os-loader-stage">{label}…</p>
      <div className="brand-os-loader-dots">
        {STAGES.map((s, i) => (
          <span key={s} className={i <= stage ? "active" : ""} />
        ))}
      </div>
    </div>
  );
}
