import "./SourceCards.css";

function pct(score) {
  if (score == null) return null;
  return Math.min(99, Math.max(0, Math.round(score <= 1 ? score * 100 : Math.min(score * 10, 100))));
}

function confidenceBadge(hybrid, globalLabel) {
  if (globalLabel) return globalLabel;
  const p = pct(hybrid);
  if (p == null) return null;
  if (p >= 70) return "High Confidence";
  if (p >= 45) return "Moderate Confidence";
  return "Low Confidence";
}

function badgeClass(label) {
  if (!label) return "";
  if (label.includes("High")) return "conf-high";
  if (label.includes("Low")) return "conf-low";
  return "conf-moderate";
}

function ScoreBar({ label, value }) {
  const p = pct(value);
  if (p == null) return null;
  return (
    <div className="source-score-row">
      <span className="source-score-label">{label}</span>
      <div className="source-score-track">
        <div className="source-score-fill" style={{ width: `${p}%` }} />
      </div>
      <span className="source-score-pct">{p}%</span>
    </div>
  );
}

export default function SourceCards({
  sources = [],
  graphConcepts = [],
  retrievalConfidence = null,
  evaluation = null,
  visible = true,
}) {
  if (!visible || (!sources.length && !graphConcepts.length)) return null;

  const globalLabel = retrievalConfidence?.label;

  return (
    <div className="source-cards" aria-label="Knowledge sources">
      <div className="source-cards-header">
        <span className="source-cards-icon">*</span>
        <span>ORB connected knowledge</span>
        {globalLabel && (
          <span className={`source-global-confidence ${badgeClass(globalLabel)}`}>
            {globalLabel}
          </span>
        )}
      </div>
      {evaluation?.source_coverage != null && (
        <p className="source-coverage-line">
          Source coverage: {Math.round(evaluation.source_coverage * 100)}%
          {evaluation.source_coverage >= 0.7 ? " ✓" : ""}
        </p>
      )}
      {sources.slice(0, 4).map((src, i) => {
        const title = src.title || src.document_title || src.file || "Knowledge";
        const category = src.category || "knowledge";
        const hybrid = src.hybrid_score ?? src.relevance_score;
        const reasons = src.retrieval_reasons || [];
        const badge = confidenceBadge(hybrid, null);

        return (
          <div key={`${title}-${i}`} className="source-card">
            <div className="source-card-top">
              <span className="source-category-chip">{category}</span>
              {badge && (
                <span className={`source-confidence ${badgeClass(badge)}`}>{badge}</span>
              )}
            </div>
            <div className="source-card-title">{title}</div>
            {src.file && <div className="source-card-file">{src.file}</div>}

            <div className="source-hybrid-scores">
              <ScoreBar label="Semantic" value={src.vector_score} />
              <ScoreBar label="Keyword" value={src.keyword_score} />
              <ScoreBar label="Graph" value={src.graph_score} />
            </div>

            {reasons.length > 0 && (
              <div className="source-retrieval-why">
                <span className="source-why-label">Retrieved because:</span>
                <ul className="source-why-list">
                  {reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      })}
      {graphConcepts.length > 0 && (
        <div className="source-graph-relations">
          <span className="source-graph-label">Related concepts</span>
          <div className="source-graph-chips">
            {graphConcepts.map((c) => (
              <span key={c} className="source-graph-chip">{c}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
