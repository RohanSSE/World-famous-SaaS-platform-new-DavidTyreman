import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import authService from "../services/authService";
import CognitionExplainability from "../components/brand-os/CognitionExplainability";
import FeedbackLearningPanel from "../components/brand-os/FeedbackLearningPanel";
import BrandOSLoading from "../components/brand-os/BrandOSLoading";
import PilotChecklist from "../components/brand-os/PilotChecklist";
import "./BrandOperatingSystem.css";

function downloadJson(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function BrandOperatingSystem() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [demos, setDemos] = useState([]);
  const [selected, setSelected] = useState("brand_dna");
  const [loading, setLoading] = useState(false);
  const [loadStage, setLoadStage] = useState(0);
  const [result, setResult] = useState(null);
  const [pilotKpis, setPilotKpis] = useState(null);
  const [showDemo, setShowDemo] = useState(false);

  const refreshPilotKpis = useCallback((sid) => {
    if (!sid) return;
    authService.getSessionPilotKpis(sid).then(setPilotKpis).catch(() => setPilotKpis(null));
  }, []);

  useEffect(() => {
    const sid =
      localStorage.getItem("sessionId") ||
      JSON.parse(localStorage.getItem("session") || "{}")?.id;
    if (sid) {
      setSessionId(String(sid));
      refreshPilotKpis(String(sid));
    } else toast.warn("No active session — open from your dashboard first.");

    authService.listBrandWorkflows().then((d) => setWorkflows(d.workflows || [])).catch(() => {});
    authService.listDemoBrands().then((d) => setDemos(d.demos || [])).catch(() => {});
  }, [refreshPilotKpis]);

  useEffect(() => {
    if (!loading) return undefined;
    const t = setInterval(() => setLoadStage((s) => (s < 3 ? s + 1 : s)), 2200);
    return () => clearInterval(t);
  }, [loading]);

  const runWorkflow = useCallback(
    async (workflowId) => {
      if (!sessionId) {
        toast.error("Select a session from User Dashboard first.");
        return;
      }
      setLoading(true);
      setLoadStage(0);
      setResult(null);
      try {
        const data = await authService.runBrandWorkflow(sessionId, workflowId);
        setResult(data);
        setSelected(workflowId);
        toast.success(`${data.canonical_workflow || workflowId} complete`);
        refreshPilotKpis(sessionId);
      } catch (e) {
        toast.error(e.message || "Workflow failed");
      } finally {
        setLoading(false);
      }
    },
    [sessionId, refreshPilotKpis]
  );

  const runDemoPack = async (demoId) => {
    if (!sessionId) {
      toast.error("Select a session first.");
      return;
    }
    setLoading(true);
    setLoadStage(0);
    try {
      const data = await authService.runDemoPack(sessionId, demoId);
      setResult({ ...data, workflow: "pack", canonical_workflow: "pack" });
      setSelected("pack");
      setShowDemo(false);
      toast.success("Demo intelligence pack ready");
      refreshPilotKpis(sessionId);
    } catch (e) {
      toast.error(e.message || "Demo failed");
    } finally {
      setLoading(false);
    }
  };

  const exportPack = async (format = "json", styled = false) => {
    if (!sessionId) return;
    setLoading(true);
    try {
      if (format === "json") {
        const data = await authService.exportBrandPack(sessionId, "pack");
        downloadJson(`brand-os-${sessionId}.json`, data.export || data);
        toast.success("Brand pack JSON downloaded");
      } else {
        await authService.downloadBrandExport(sessionId, "pack", format, styled);
        toast.success(`Brand pack ${format.toUpperCase()} downloaded`);
      }
      authService.recordPilotEvent(sessionId, "export", { workflow: "pack", format }).catch(() => {});
      refreshPilotKpis(sessionId);
    } catch (e) {
      toast.error(e.message || "Export failed");
    } finally {
      setLoading(false);
    }
  };

  const explainability = result?.explainability || {
    reasoning_path: result?.reasoning_path,
    sources: result?.sources,
    critique_flags: result?.critique_flags,
    strategic_consistency: result?.strategic_consistency,
    verification: result?.verification,
  };

  return (
    <div className="brand-os-page">
      <header className="brand-os-header">
        <div>
          <h1>AI Brand Operating System</h1>
          <p className="brand-os-sub">
            Evidence-grounded strategic cognition — validate with real brands, export premium deliverables.
          </p>
        </div>
        <div className="brand-os-header-actions">
          <button type="button" className="brand-os-ghost" onClick={() => navigate("/user-dashboard")}>
            Dashboard
          </button>
          <button type="button" className="brand-os-ghost" onClick={() => navigate("/brand-onboarding")}>
            Onboarding
          </button>
          <button type="button" className="brand-os-demo-btn" onClick={() => setShowDemo(true)} disabled={loading}>
            One-Click Demo
          </button>
          <button type="button" className="brand-os-primary" onClick={() => runWorkflow("pack")} disabled={loading}>
            Full Brand Pack
          </button>
          <button type="button" className="brand-os-ghost" onClick={() => exportPack("pdf", true)} disabled={loading}>
            Premium PDF
          </button>
        </div>
      </header>

      {pilotKpis && (
        <div className="brand-os-pilot-bar">
          <span>Exports: {pilotKpis.export_downloads}</span>
          <span>Edits: {pilotKpis.user_edits}</span>
          <span>Workflows: {pilotKpis.workflow_runs}</span>
          <span>Engagement: {pilotKpis.engagement_score}</span>
        </div>
      )}

      <div className="brand-os-layout">
        <nav className="brand-os-workflows">
          <h2>Workflows</h2>
          <ul>
            {workflows.map((w) => (
              <li key={w.id}>
                <button
                  type="button"
                  className={selected === w.id ? "active" : ""}
                  disabled={loading}
                  onClick={() => runWorkflow(w.canonical_id || w.id)}
                >
                  {w.label || w.id}
                </button>
              </li>
            ))}
          </ul>
          {pilotKpis?.pilot_checklist && (
            <PilotChecklist
              checklist={pilotKpis.pilot_checklist}
              completionPct={pilotKpis.pilot_completion_pct}
            />
          )}
          <p className="brand-os-session">Session #{sessionId || "—"}</p>
        </nav>

        <main className="brand-os-main brand-os-main-animate">
          {loading && <BrandOSLoading stage={loadStage} visible />}
          {!loading && result?.narrative && (
            <article className="brand-os-narrative">
              {result.demo && <span className="brand-os-demo-badge">Demo pack</span>}
              <h2>{result.canonical_workflow || result.workflow}</h2>
              <div className="brand-os-narrative-body">
                {result.narrative.split("\n").map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            </article>
          )}
          {!loading && result?.brand_operating_system && !result?.narrative && (
            <article className="brand-os-structured">
              <h2>Brand Operating System package</h2>
              <pre>{JSON.stringify(result.brand_operating_system, null, 2)}</pre>
            </article>
          )}
          {!loading && !result && (
            <div className="brand-os-empty-state">
              <h2>Start your pilot run</h2>
              <p>
                Upload brand PDFs and founder notes, then run a workflow — or use One-Click Demo for
                investor-ready output in seconds.
              </p>
              <button type="button" className="brand-os-primary" onClick={() => setShowDemo(true)}>
                Generate Full Brand Intelligence Pack
              </button>
            </div>
          )}
        </main>

        <aside className="brand-os-aside">
          <CognitionExplainability
            explainability={explainability}
            evaluation={result?.evaluation}
            narrative={result?.narrative}
            visible={!!result && !loading}
          />
          <FeedbackLearningPanel
            sessionId={sessionId}
            lastOutput={result?.narrative || ""}
            onSaved={() => refreshPilotKpis(sessionId)}
          />
        </aside>
      </div>

      {showDemo && (
        <div className="brand-os-modal-overlay" onClick={() => setShowDemo(false)} role="presentation">
          <div className="brand-os-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Demo brand packs</h2>
            <p>Instant intelligence for client and investor demos.</p>
            <div className="brand-os-demo-grid">
              {demos.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className="brand-os-demo-card"
                  onClick={() => runDemoPack(d.id)}
                  disabled={loading}
                >
                  <strong>{d.label}</strong>
                  <span>{d.tagline}</span>
                </button>
              ))}
            </div>
            <button type="button" className="brand-os-ghost" onClick={() => setShowDemo(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
