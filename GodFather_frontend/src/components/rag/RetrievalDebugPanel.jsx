import { useState } from "react";
import "./RetrievalDebugPanel.css";

export default function RetrievalDebugPanel({ debug, insights = [], visible = true }) {
  const [open, setOpen] = useState(false);
  if (!visible || !debug) return null;

  const chunks = debug.chunks_ranked || [];
  const agents = debug.selected_agents || [];

  return (
    <div className="retrieval-debug">
      <button
        type="button"
        className="retrieval-debug-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {open ? "Hide" : "Show"} retrieval debug
      </button>
      {open && (
        <div className="retrieval-debug-body">
          <section>
            <h4>Planner</h4>
            <p className="debug-line">
              Primary: <strong>{debug.primary_agent || debug.agent_id}</strong>
              {" · "}
              Agents: {agents.join(", ") || "—"}
              {debug.intent && <> · Intent: {debug.intent}</>}
            </p>
          </section>

          {insights?.length > 0 && (
            <section>
              <h4>Strategic insights</h4>
              <ul className="debug-insights">
                {insights.map((i) => (
                  <li key={i.type}>{i.message}</li>
                ))}
              </ul>
            </section>
          )}

          {debug.graph_concepts?.length > 0 && (
            <section>
              <h4>Graph concepts</h4>
              <div className="debug-chips">
                {debug.graph_concepts.map((c) => (
                  <span key={c} className="debug-chip">{c}</span>
                ))}
              </div>
            </section>
          )}

          {debug.memory_snippets?.length > 0 && (
            <section>
              <h4>Memory hits</h4>
              <ul className="debug-memory">
                {debug.memory_snippets.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h4>Rerank order ({chunks.length})</h4>
            <table className="debug-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Cat</th>
                  <th>Hybrid</th>
                  <th>V</th>
                  <th>K</th>
                  <th>G</th>
                  <th>Title</th>
                </tr>
              </thead>
              <tbody>
                {chunks.map((c) => (
                  <tr key={c.rank}>
                    <td>{c.rank}</td>
                    <td>{c.category}</td>
                    <td>{c.hybrid_score ?? "—"}</td>
                    <td>{c.vector_score ?? "—"}</td>
                    <td>{c.keyword_score ?? "—"}</td>
                    <td>{c.graph_score ?? "—"}</td>
                    <td title={c.title}>{c.title || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {chunks[0]?.retrieval_reasons?.length > 0 && (
              <p className="debug-reasons">
                Top reasons: {chunks[0].retrieval_reasons.join(" · ")}
              </p>
            )}
          </section>

          {debug.latency_ms != null && (
            <p className="debug-latency">Latency: {debug.latency_ms}ms</p>
          )}
        </div>
      )}
    </div>
  );
}
