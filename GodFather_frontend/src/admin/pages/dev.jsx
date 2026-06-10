import { useEffect, useMemo, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { DashboardContent } from "@admin/layouts/dashboard/content";
import adminApi from "@admin/lib/adminApi";

const PRE_RETRIEVAL_PLACEHOLDER =
  "Example:\nFocus retrieval on high-signal manifesto and positioning evidence for trust and differentiation. Prefer chunks that include explicit principles, concrete language, and strategic tags (trust, authority, positioning). Avoid generic marketing advice and trend-chasing language.";

const SYSTEM_INJECTION_PLACEHOLDER =
  "Example:\nWhen evidence is weak, answer conservatively and state uncertainty. Prioritize manifesto-aligned reasoning and cite source titles in the response. Do not overclaim; if two chunks conflict, reconcile toward trust, consistency, and brand promise before final output.";

const PROFILE_NOTES_PLACEHOLDER =
  "Example:\nSprint target: improve retrieval precision on trust queries from 0.53 to >0.75.\nCurrent issue: weak_manifesto_grounding and generic_reasoning.\nOperator strategy: enforce manifesto-first alignment and stronger contradiction handling.";

const PHASE_PROMPT_PLACEHOLDERS = {
  phase_1_master_prompt:
    "Example:\nDiscovery goal: identify audience truth, buying tension, category context, and strategic constraints with clear evidence.",
  phase_2_master_prompt:
    "Example:\nBrand Book/Playbook goal: codify DNA, voice, and non-negotiables into reusable operating rules.",
  phase_3_master_prompt:
    "Example:\nPromotion goal: generate channel-ready campaigns grounded in manifesto consistency and differentiated positioning.",
  phase_4_master_prompt:
    "Example:\nStrategic Guidance & Content goal: provide high-confidence guidance and concrete content with rationale and source grounding.",
};

const PRESET_LIBRARY = {
  trust: {
    label: "Trust tuning",
    pre_retrieval_prompt:
      "Prioritize chunks with explicit trust evidence: consistency, promise-keeping, credibility, authority, authenticity. Prefer manifesto and branding anchors with concrete strategic language. Penalize generic growth-marketing suggestions and vague inspiration-only content.",
    system_injection_prompt:
      "Respond with trust-first strategic reasoning. Every major claim should map to retrieved evidence. If evidence is weak, use conservative phrasing and ask a clarifying follow-up rather than overclaiming. Avoid hype language.",
    retrieval_profile_notes:
      "Mode: Trust tuning. KPI target: raise retrieval precision and groundedness on trust/authority prompts. Watch for weak_manifesto_grounding and unsupported_claim flags.",
  },
  differentiation: {
    label: "Differentiation tuning",
    pre_retrieval_prompt:
      "Favor chunks about unique positioning, category framing, competitive separation, value asymmetry, and market enemy logic. Prioritize positioning + strategy + manifesto signals. Down-rank generic advice and copycat language.",
    system_injection_prompt:
      "Generate outputs that force distinctiveness: name the strategic wedge, what is rejected, and how competitors are made irrelevant. Keep guidance evidence-backed and specific, with explicit anti-generic stance.",
    retrieval_profile_notes:
      "Mode: Differentiation tuning. KPI target: improve top-1 strategic relevance for positioning queries. Monitor generic_reasoning cluster and top1_miss_rate for differentiation intent.",
  },
  manifesto: {
    label: "Manifesto grounding",
    pre_retrieval_prompt:
      "Reserve retrieval attention for manifesto/brand-book chunks with principles, non-negotiables, promise, and brand DNA. Ensure at least two high-signal anchor chunks from manifesto-aligned sources before supporting context.",
    system_injection_prompt:
      "Keep response anchored in manifesto principles and brand promise. If context conflicts, reconcile toward manifesto and consistency over novelty. Cite source-backed rationale and suppress speculative claims.",
    retrieval_profile_notes:
      "Mode: Manifesto grounding. KPI target: increase manifesto_dominance and source_coverage on strategic queries. Reduce context_conflict and overclaim rates.",
  },
};

export default function RagDevPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [config, setConfig] = useState({
    active_pipeline: "rag_v1",
    enabled: false,
    pre_retrieval_prompt: "",
    system_injection_prompt: "",
    retrieval_profile_notes: "",
    phase_1_master_prompt: "",
    phase_2_master_prompt: "",
    phase_3_master_prompt: "",
    phase_4_master_prompt: "",
  });

  const [indexStatus, setIndexStatus] = useState(null);

  const [testForm, setTestForm] = useState({
    query: "How should a premium brand build trust without sounding generic?",
    session_id: "",
    top_k: 8,
    include_user_docs: false,
    agent_id: "strategist",
    pipeline: "",
    pre_retrieval_prompt: "",
    system_injection_prompt: "",
  });

  const [testResult, setTestResult] = useState(null);

  const applyPreset = (presetKey, target = "global") => {
    const preset = PRESET_LIBRARY[presetKey];
    if (!preset) return;

    if (target === "test") {
      setTestForm((prev) => ({
        ...prev,
        pre_retrieval_prompt: preset.pre_retrieval_prompt,
        system_injection_prompt: preset.system_injection_prompt,
      }));
      setSuccess(`${preset.label} applied to one-time test overrides.`);
      return;
    }

    setConfig((prev) => ({
      ...prev,
      enabled: true,
      pre_retrieval_prompt: preset.pre_retrieval_prompt,
      system_injection_prompt: preset.system_injection_prompt,
      retrieval_profile_notes: preset.retrieval_profile_notes,
    }));
    setSuccess(`${preset.label} loaded into global injection fields. Click Save Global Injection to activate.`);
  };

  const loadAll = async () => {
    setLoading(true);
    setError("");
    try {
      const [cfg, idx] = await Promise.all([
        adminApi.ragDevConfig(),
        adminApi.ragDevIndexStatus(),
      ]);
      setConfig({
        active_pipeline: cfg.active_pipeline || "rag_v1",
        enabled: !!cfg.enabled,
        pre_retrieval_prompt: cfg.pre_retrieval_prompt || "",
        system_injection_prompt: cfg.system_injection_prompt || "",
        retrieval_profile_notes: cfg.retrieval_profile_notes || "",
        phase_1_master_prompt: cfg.phase_1_master_prompt || "",
        phase_2_master_prompt: cfg.phase_2_master_prompt || "",
        phase_3_master_prompt: cfg.phase_3_master_prompt || "",
        phase_4_master_prompt: cfg.phase_4_master_prompt || "",
      });
      setIndexStatus(idx);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed to load RAG Dev data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleConfigChange = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const saveConfig = async () => {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const saved = await adminApi.saveRagDevConfig(config);
      setConfig({
        active_pipeline: saved.active_pipeline || "rag_v1",
        enabled: !!saved.enabled,
        pre_retrieval_prompt: saved.pre_retrieval_prompt || "",
        system_injection_prompt: saved.system_injection_prompt || "",
        retrieval_profile_notes: saved.retrieval_profile_notes || "",
        phase_1_master_prompt: saved.phase_1_master_prompt || "",
        phase_2_master_prompt: saved.phase_2_master_prompt || "",
        phase_3_master_prompt: saved.phase_3_master_prompt || "",
        phase_4_master_prompt: saved.phase_4_master_prompt || "",
      });
      setSuccess("RAG dev config saved and live for subsequent queries.");
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  const rebuildIndex = async (force = true, asyncBuild = true) => {
    setRebuilding(true);
    setError("");
    setSuccess("");
    try {
      const res = await adminApi.ragDevRebuildIndex({
        force,
        async_build: asyncBuild,
      });
      setSuccess(res.message || "Index rebuild requested.");
      const idx = await adminApi.ragDevIndexStatus();
      setIndexStatus(idx);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed to trigger rebuild");
    } finally {
      setRebuilding(false);
    }
  };

  const runTestQuery = async () => {
    if (!testForm.query.trim()) {
      setError("Test query is required");
      return;
    }

    setTesting(true);
    setError("");
    setSuccess("");
    setTestResult(null);

    try {
      const payload = {
        query: testForm.query,
        session_id: testForm.session_id ? Number(testForm.session_id) : undefined,
        top_k: Number(testForm.top_k) || 8,
        include_user_docs: !!testForm.include_user_docs,
        agent_id: testForm.agent_id || "strategist",
        pipeline: testForm.pipeline || undefined,
        pre_retrieval_prompt: testForm.pre_retrieval_prompt,
        system_injection_prompt: testForm.system_injection_prompt,
      };
      const res = await adminApi.ragDevTestQuery(payload);
      setTestResult(res);
      setSuccess("Test query completed.");
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Test query failed");
    } finally {
      setTesting(false);
    }
  };

  const statusChip = useMemo(() => {
    if (!indexStatus) return null;
    if (indexStatus.index_exists && !indexStatus.needs_rebuild) {
      return <Chip size="small" color="success" label="Index healthy" />;
    }
    if (!indexStatus.index_exists) {
      return <Chip size="small" color="error" label="Index missing" />;
    }
    return <Chip size="small" color="warning" label="Rebuild recommended" />;
  }, [indexStatus]);

  return (
    <DashboardContent maxWidth="xl">
      <Stack spacing={2}>
        <Box>
          <Typography variant="h4">RAG Dev Console</Typography>
          <Typography variant="body2" color="text.secondary">
            Fine-tune retrieval behavior, run index rebuilds, and inject human operator prompts into the active RAG pipeline.
          </Typography>
        </Box>

        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}

        {loading ? (
          <Card sx={{ p: 4, display: "flex", justifyContent: "center" }}>
            <CircularProgress />
          </Card>
        ) : (
          <>
            <Card sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="h6">Index Health & Training Controls</Typography>
                  {statusChip}
                </Stack>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Typography variant="body2" color="text.secondary">Index exists</Typography>
                    <Typography variant="subtitle1">{String(!!indexStatus?.index_exists)}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Typography variant="body2" color="text.secondary">Document count</Typography>
                    <Typography variant="subtitle1">{indexStatus?.doc_count ?? "—"}</Typography>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Typography variant="body2" color="text.secondary">Needs rebuild</Typography>
                    <Typography variant="subtitle1">{String(!!indexStatus?.needs_rebuild)} ({indexStatus?.reason || "n/a"})</Typography>
                  </Grid>
                </Grid>

                <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                  <Button
                    variant="contained"
                    onClick={() => rebuildIndex(true, true)}
                    disabled={rebuilding}
                  >
                    {rebuilding ? "Rebuilding..." : "Rebuild Knowledge Index (Async)"}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => rebuildIndex(true, false)}
                    disabled={rebuilding}
                  >
                    Rebuild Knowledge Index (Sync)
                  </Button>
                  <Button variant="text" onClick={loadAll} disabled={rebuilding || loading}>
                    Refresh Status
                  </Button>
                </Stack>
              </Stack>
            </Card>

            <Card sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Typography variant="h6">Live Prompt Injection (Global)</Typography>
                <Alert severity="info">
                  These fields are injected into the existing RAG mechanism. Keep instructions precise, evidence-first, and measurable.
                </Alert>

                <Stack spacing={1}>
                  <Typography variant="subtitle2">Preset Library (one click)</Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                    <Button variant="outlined" onClick={() => applyPreset("trust", "global")}>
                      Trust tuning
                    </Button>
                    <Button variant="outlined" onClick={() => applyPreset("differentiation", "global")}>
                      Differentiation tuning
                    </Button>
                    <Button variant="outlined" onClick={() => applyPreset("manifesto", "global")}>
                      Manifesto grounding
                    </Button>
                  </Stack>
                </Stack>

                <FormControlLabel
                  control={
                    <Switch
                      checked={!!config.enabled}
                      onChange={(e) => handleConfigChange("enabled", e.target.checked)}
                    />
                  }
                  label="Enable global operator injection"
                />

                <TextField
                  select
                  label="Active pipeline"
                  value={config.active_pipeline}
                  onChange={(e) => handleConfigChange("active_pipeline", e.target.value)}
                >
                  <MenuItem value="rag_v1">RAG v1 (legacy stable)</MenuItem>
                  <MenuItem value="rag_v2">RAG v2 (phase-driven)</MenuItem>
                </TextField>

                <TextField
                  label="Pre-retrieval guidance"
                  value={config.pre_retrieval_prompt}
                  onChange={(e) => handleConfigChange("pre_retrieval_prompt", e.target.value)}
                  multiline
                  minRows={5}
                  placeholder={PRE_RETRIEVAL_PLACEHOLDER}
                />

                <TextField
                  label="System-level generation injection"
                  value={config.system_injection_prompt}
                  onChange={(e) => handleConfigChange("system_injection_prompt", e.target.value)}
                  multiline
                  minRows={5}
                  placeholder={SYSTEM_INJECTION_PLACEHOLDER}
                />

                <TextField
                  label="Retrieval profile notes"
                  value={config.retrieval_profile_notes}
                  onChange={(e) => handleConfigChange("retrieval_profile_notes", e.target.value)}
                  multiline
                  minRows={4}
                  placeholder={PROFILE_NOTES_PLACEHOLDER}
                />

                <Divider />
                <Typography variant="subtitle1">RAGv2 Phase Master Prompts</Typography>
                <Typography variant="body2" color="text.secondary">
                  These prompts define target outcomes for each phase when the active pipeline is RAG v2.
                </Typography>

                <TextField
                  label="Phase 1: Discovery goal"
                  value={config.phase_1_master_prompt}
                  onChange={(e) => handleConfigChange("phase_1_master_prompt", e.target.value)}
                  multiline
                  minRows={3}
                  placeholder={PHASE_PROMPT_PLACEHOLDERS.phase_1_master_prompt}
                />

                <TextField
                  label="Phase 2: Brand Book / Playbook goal"
                  value={config.phase_2_master_prompt}
                  onChange={(e) => handleConfigChange("phase_2_master_prompt", e.target.value)}
                  multiline
                  minRows={3}
                  placeholder={PHASE_PROMPT_PLACEHOLDERS.phase_2_master_prompt}
                />

                <TextField
                  label="Phase 3: Brand Promotion goal"
                  value={config.phase_3_master_prompt}
                  onChange={(e) => handleConfigChange("phase_3_master_prompt", e.target.value)}
                  multiline
                  minRows={3}
                  placeholder={PHASE_PROMPT_PLACEHOLDERS.phase_3_master_prompt}
                />

                <TextField
                  label="Phase 4: Strategic Guidance & Content Creation goal"
                  value={config.phase_4_master_prompt}
                  onChange={(e) => handleConfigChange("phase_4_master_prompt", e.target.value)}
                  multiline
                  minRows={3}
                  placeholder={PHASE_PROMPT_PLACEHOLDERS.phase_4_master_prompt}
                />

                <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                  <Button variant="contained" onClick={saveConfig} disabled={saving}>
                    {saving ? "Saving..." : "Save Global Injection"}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() =>
                      setConfig({
                        active_pipeline: "rag_v1",
                        enabled: false,
                        pre_retrieval_prompt: "",
                        system_injection_prompt: "",
                        retrieval_profile_notes: "",
                        phase_1_master_prompt: "",
                        phase_2_master_prompt: "",
                        phase_3_master_prompt: "",
                        phase_4_master_prompt: "",
                      })
                    }
                    disabled={saving}
                  >
                    Clear Form
                  </Button>
                </Stack>
              </Stack>
            </Card>

            <Card sx={{ p: 3 }}>
              <Stack spacing={2}>
                <Typography variant="h6">A/B Test Query (One-time Override)</Typography>
                <Typography variant="body2" color="text.secondary">
                  Run a query through the full RAG pipeline with temporary prompt injection overrides. This does not overwrite global config unless you save above.
                </Typography>

                <Stack spacing={1}>
                  <Typography variant="subtitle2">Test Presets</Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                    <Button variant="text" onClick={() => applyPreset("trust", "test")}>
                      Apply Trust tuning to test
                    </Button>
                    <Button variant="text" onClick={() => applyPreset("differentiation", "test")}>
                      Apply Differentiation to test
                    </Button>
                    <Button variant="text" onClick={() => applyPreset("manifesto", "test")}>
                      Apply Manifesto to test
                    </Button>
                  </Stack>
                </Stack>

                <TextField
                  label="Test query"
                  value={testForm.query}
                  onChange={(e) => setTestForm((p) => ({ ...p, query: e.target.value }))}
                  multiline
                  minRows={2}
                />

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      label="Session ID (optional)"
                      value={testForm.session_id}
                      onChange={(e) => setTestForm((p) => ({ ...p, session_id: e.target.value }))}
                      fullWidth
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      label="Top K"
                      type="number"
                      value={testForm.top_k}
                      onChange={(e) => setTestForm((p) => ({ ...p, top_k: e.target.value }))}
                      fullWidth
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      label="Agent"
                      value={testForm.agent_id}
                      onChange={(e) => setTestForm((p) => ({ ...p, agent_id: e.target.value }))}
                      fullWidth
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <TextField
                      select
                      label="Pipeline override"
                      value={testForm.pipeline}
                      onChange={(e) => setTestForm((p) => ({ ...p, pipeline: e.target.value }))}
                      fullWidth
                    >
                      <MenuItem value="">Use active pipeline</MenuItem>
                      <MenuItem value="rag_v1">Force RAG v1</MenuItem>
                      <MenuItem value="rag_v2">Force RAG v2</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 3 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={!!testForm.include_user_docs}
                          onChange={(e) => setTestForm((p) => ({ ...p, include_user_docs: e.target.checked }))}
                        />
                      }
                      label="Include user docs"
                    />
                  </Grid>
                </Grid>

                <TextField
                  label="One-time pre-retrieval override"
                  value={testForm.pre_retrieval_prompt}
                  onChange={(e) => setTestForm((p) => ({ ...p, pre_retrieval_prompt: e.target.value }))}
                  multiline
                  minRows={4}
                  placeholder={PRE_RETRIEVAL_PLACEHOLDER}
                />

                <TextField
                  label="One-time system injection override"
                  value={testForm.system_injection_prompt}
                  onChange={(e) => setTestForm((p) => ({ ...p, system_injection_prompt: e.target.value }))}
                  multiline
                  minRows={4}
                  placeholder={SYSTEM_INJECTION_PLACEHOLDER}
                />

                <Stack direction="row" spacing={1}>
                  <Button variant="contained" onClick={runTestQuery} disabled={testing}>
                    {testing ? "Running..." : "Run Test Query"}
                  </Button>
                </Stack>

                {testResult && (
                  <>
                    <Divider />
                    <Typography variant="subtitle1">Answer</Typography>
                    <Card variant="outlined" sx={{ p: 2, whiteSpace: "pre-wrap" }}>
                      <Typography variant="body2">{testResult.answer || "No answer returned."}</Typography>
                    </Card>

                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <Typography variant="body2" color="text.secondary">Chunks Retrieved</Typography>
                        <Typography variant="subtitle1">{testResult.chunks_retrieved ?? "—"}</Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <Typography variant="body2" color="text.secondary">Retrieval Confidence</Typography>
                        <Typography variant="subtitle1">{testResult.retrieval_confidence?.label || testResult.retrieval_confidence?.mode || "—"}</Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <Typography variant="body2" color="text.secondary">Latency</Typography>
                        <Typography variant="subtitle1">{testResult.latency_breakdown?.total_ms ? `${testResult.latency_breakdown.total_ms} ms` : "—"}</Typography>
                      </Grid>
                    </Grid>

                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="body2" color="text.secondary">Active Pipeline</Typography>
                        <Typography variant="subtitle1">{testResult.active_pipeline || "—"}</Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="body2" color="text.secondary">Resolved RAG Phase</Typography>
                        <Typography variant="subtitle1">{testResult.rag_phase || "—"}</Typography>
                      </Grid>
                    </Grid>

                    <Typography variant="subtitle1">Sources</Typography>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" component="pre" sx={{ m: 0, whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(testResult.sources || [], null, 2)}
                      </Typography>
                    </Card>

                    <Typography variant="subtitle1">Retrieval Debug</Typography>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" component="pre" sx={{ m: 0, whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(testResult.retrieval_debug || {}, null, 2)}
                      </Typography>
                    </Card>

                    <Typography variant="subtitle1">Phase Artifacts</Typography>
                    <Card variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="body2" component="pre" sx={{ m: 0, whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(testResult.phase_artifacts || {}, null, 2)}
                      </Typography>
                    </Card>
                  </>
                )}
              </Stack>
            </Card>
          </>
        )}
      </Stack>
    </DashboardContent>
  );
}
