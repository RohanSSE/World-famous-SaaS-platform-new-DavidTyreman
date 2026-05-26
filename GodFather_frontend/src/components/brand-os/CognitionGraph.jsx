import "./CognitionGraph.css";

const STATUS_COLOR = {
  grounded: "#3dd68c",
  partial: "#ffb86c",
  unsupported: "#ff6b6b",
  drift_risk: "#c084fc",
};

export default function CognitionGraph({ reasoningPath = [], visible = true }) {
  if (!visible || !reasoningPath?.length) return null;

  return (
    <div className="cognition-graph" aria-label="Cognition reasoning graph">
      <p className="cognition-graph-label">Cognition graph</p>
      <div className="cognition-graph-track">
        {reasoningPath.slice(0, 8).map((step, i) => {
          const status = step.verification_status || (step.grounded ? "grounded" : "partial");
          const color = STATUS_COLOR[status] || STATUS_COLOR.partial;
          const claim = (step.claim || step.summary || step.detail || `Step ${i + 1}`).slice(0, 120);
          return (
            <div key={i} className="cognition-graph-node-wrap">
              {i > 0 && <div className="cognition-graph-edge" />}
              <div className="cognition-graph-node" style={{ borderColor: color }}>
                <span className="cognition-graph-status" style={{ background: color }} />
                <span className="cognition-graph-claim">{claim}</span>
                {step.risk != null && (
                  <span className="cognition-graph-risk">risk {(step.risk * 100).toFixed(0)}%</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
