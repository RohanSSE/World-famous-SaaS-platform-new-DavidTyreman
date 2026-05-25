import SourceCards from "../rag/SourceCards";
import CognitionGraph from "./CognitionGraph";
import "./CognitionExplainability.css";

function pct(v) {
  if (v == null || Number.isNaN(v)) return null;
  const n = Number(v);
  return Math.round(n <= 1 ? n * 100 : Math.min(n * 10, 100));
}

export default function CognitionExplainability({
  explainability = {},
  evaluation = null,
  narrative = "",
  visible = true,
}) {
  if (!visible) return null;

  const {
    reasoning_path: reasoningPath = [],
    sources = [],
    critique_flags: critiqueFlags = [],
    strategic_consistency: consistency = {},
    verification = {},
  } = explainability;

  const conf =
    evaluation?.retrieval_confidence ??
    evaluation?.confidence ??
    verification?.confidence;
  const confPct = pct(conf);
  const consistencyScore = pct(
    consistency?.score ?? consistency?.consistency_score ?? evaluation?.consistency_score
  );

  return (
    <aside className="cognition-explain" aria-label="Cognition explainability">
      <h3 className="cognition-explain-title">Why this output</h3>

      {confPct != null && (
        <div className="cognition-meter">
          <span>Confidence</span>
          <div className="cognition-meter-track">
            <div className="cognition-meter-fill" style={{ width: `${confPct}%` }} />
          </div>
          <span className="cognition-meter-val">{confPct}%</span>
        </div>
      )}

      {consistencyScore != null && (
        <div className="cognition-meter">
          <span>Brand consistency</span>
          <div className="cognition-meter-track consistency">
            <div className="cognition-meter-fill" style={{ width: `${consistencyScore}%` }} />
          </div>
          <span className="cognition-meter-val">{consistencyScore}%</span>
        </div>
      )}

      {critiqueFlags?.length > 0 && (
        <div className="cognition-warnings">
          <p className="cognition-warn-label">Contradiction / critique flags</p>
          <ul>
            {critiqueFlags.map((f, i) => (
              <li key={i}>{typeof f === "string" ? f : f.message || JSON.stringify(f)}</li>
            ))}
          </ul>
        </div>
      )}

      <CognitionGraph reasoningPath={reasoningPath} visible={reasoningPath?.length > 0} />

      {reasoningPath?.length > 0 && (
        <div className="cognition-reasoning">
          <p className="cognition-section-label">Reasoning path</p>
          <ol>
            {reasoningPath.map((step, i) => (
              <li key={i}>
                <strong>{step.stage || step.step || `Step ${i + 1}`}</strong>
                {step.detail && <span> — {step.detail}</span>}
                {step.summary && <p>{step.summary}</p>}
              </li>
            ))}
          </ol>
        </div>
      )}

      <SourceCards
        sources={sources}
        evaluation={evaluation}
        visible={sources.length > 0}
      />

      {verification?.unsupported_claims?.length > 0 && (
        <div className="cognition-evidence">
          <p className="cognition-section-label">Unsupported claims (repaired)</p>
          <ul>
            {verification.unsupported_claims.slice(0, 5).map((c, i) => (
              <li key={i}>{typeof c === "string" ? c : c.claim || c.text}</li>
            ))}
          </ul>
        </div>
      )}

      {narrative && (
        <details className="cognition-output-preview">
          <summary>Full narrative</summary>
          <pre>{narrative}</pre>
        </details>
      )}
    </aside>
  );
}
