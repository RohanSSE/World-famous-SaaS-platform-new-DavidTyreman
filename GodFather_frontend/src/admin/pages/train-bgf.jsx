import { useEffect, useMemo, useState } from "react";

import Alert from "@mui/material/Alert";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";

import adminApi from "@admin/lib/adminApi";
import { DashboardContent } from "@admin/layouts/dashboard/content";

const SECTION_CONFIG = [
  {
    id: 1,
    key: "phase_1_master_prompt",
    title: "Fine Tune the Discovery Phase",
  },
  {
    id: 2,
    key: "phase_2_master_prompt",
    title: "Fine Tune the BrandBook Phase",
  },
  {
    id: 3,
    key: "phase_3_master_prompt",
    title: "Fine Tune Content Generation Phase",
  },
  {
    id: 4,
    key: "phase_4_master_prompt",
    title: "Fine Tune Ongoing Guidance Phase",
  },
];

function emptySectionState() {
  return {
    mandatory_prompt: "",
    prompt: "",
    goal: "",
    criteria: "",
  };
}

function parsePhasePrompt(value = "") {
  const text = String(value || "");
  const promptMatch = text.match(/\[Prompt\]\s*([\s\S]*?)(?=\n\[Goal\]|$)/i);
  const goalMatch = text.match(/\[Goal\]\s*([\s\S]*?)(?=\n\[Evaluation Criteria\]|$)/i);
  const criteriaMatch = text.match(/\[Evaluation Criteria\]\s*([\s\S]*?)$/i);

  if (promptMatch || goalMatch || criteriaMatch) {
    return {
      prompt: (promptMatch?.[1] || "").trim(),
      goal: (goalMatch?.[1] || "").trim(),
      criteria: (criteriaMatch?.[1] || "").trim(),
    };
  }

  return { prompt: text.trim(), goal: "", criteria: "" };
}

export default function TrainBgfPage() {
  const [loading, setLoading] = useState(true);
  const [loadingDefault, setLoadingDefault] = useState(false);
  const [savingBySection, setSavingBySection] = useState({});
  const [trainingBySection, setTrainingBySection] = useState({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [engine, setEngine] = useState("rag_v1");
  const [sections, setSections] = useState(() => ({
    phase_1_master_prompt: emptySectionState(),
    phase_2_master_prompt: emptySectionState(),
    phase_3_master_prompt: emptySectionState(),
    phase_4_master_prompt: emptySectionState(),
  }));
  const [versions, setVersions] = useState([]);
  const [defaultTemplate, setDefaultTemplate] = useState(null);
  const [expandedVersionId, setExpandedVersionId] = useState(null);

  const hydrateFromConfig = (cfg = {}, providedSections = null) => {
    setEngine(cfg.active_pipeline || "rag_v1");
    if (providedSections && typeof providedSections === "object") {
      setSections({
        phase_1_master_prompt: {
          ...emptySectionState(),
          ...(providedSections.phase_1_master_prompt || {}),
        },
        phase_2_master_prompt: {
          ...emptySectionState(),
          ...(providedSections.phase_2_master_prompt || {}),
        },
        phase_3_master_prompt: {
          ...emptySectionState(),
          ...(providedSections.phase_3_master_prompt || {}),
        },
        phase_4_master_prompt: {
          ...emptySectionState(),
          ...(providedSections.phase_4_master_prompt || {}),
        },
      });
      return;
    }

    setSections({
      phase_1_master_prompt: {
        ...emptySectionState(),
        ...parsePhasePrompt(cfg.phase_1_master_prompt),
        mandatory_prompt: String(cfg.phase_1_base_prompt || "").trim(),
        prompt: String(cfg.phase_1_admin_injection_prompt || parsePhasePrompt(cfg.phase_1_master_prompt).prompt || "").trim(),
        goal: String(cfg.phase_1_admin_injection_goal || parsePhasePrompt(cfg.phase_1_master_prompt).goal || "").trim(),
        criteria: String(cfg.phase_1_admin_injection_criteria || parsePhasePrompt(cfg.phase_1_master_prompt).criteria || "").trim(),
      },
      phase_2_master_prompt: parsePhasePrompt(cfg.phase_2_master_prompt),
      phase_3_master_prompt: parsePhasePrompt(cfg.phase_3_master_prompt),
      phase_4_master_prompt: parsePhasePrompt(cfg.phase_4_master_prompt),
    });
  };

  const loadConfig = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const state = await adminApi.aiTuningState(25);
      hydrateFromConfig(state?.config || {}, state?.sections || null);
      setVersions(Array.isArray(state?.versions) ? state.versions : []);
      setDefaultTemplate(state?.default_template || null);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to load Train BGF configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const hasBusySections = useMemo(
    () =>
      Object.values(savingBySection).some(Boolean) ||
      Object.values(trainingBySection).some(Boolean),
    [savingBySection, trainingBySection]
  );

  const updateSectionField = (sectionKey, field, value) => {
    setSections((prev) => ({
      ...prev,
      [sectionKey]: {
        ...prev[sectionKey],
        [field]: value,
      },
    }));
  };

  const getSectionPayload = (sectionKey) => ({
    active_pipeline: engine,
    prompt: sections[sectionKey]?.prompt || "",
    goal: sections[sectionKey]?.goal || "",
    criteria: sections[sectionKey]?.criteria || "",
  });

  const saveSection = async (sectionKey) => {
    setSavingBySection((prev) => ({ ...prev, [sectionKey]: true }));
    setError("");
    setSuccess("");
    try {
      const res = await adminApi.aiTuningSaveSection(sectionKey, getSectionPayload(sectionKey));
      setSuccess(`Section saved successfully (v${res?.version?.version_number || "-"}).`);
      await loadConfig();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to save section");
    } finally {
      setSavingBySection((prev) => ({ ...prev, [sectionKey]: false }));
    }
  };

  const trainSection = async (sectionKey) => {
    setTrainingBySection((prev) => ({ ...prev, [sectionKey]: true }));
    setError("");
    setSuccess("");
    try {
      const res = await adminApi.aiTuningTrainSection(sectionKey, getSectionPayload(sectionKey));
      setSuccess(
        `Training started for ${sectionKey}. ${res?.message || "Section-specific train request submitted."}`
      );
      await loadConfig();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to start training");
    } finally {
      setTrainingBySection((prev) => ({ ...prev, [sectionKey]: false }));
    }
  };

  const loadDefault = async () => {
    setLoadingDefault(true);
    setError("");
    setSuccess("");
    try {
      const res = await adminApi.aiTuningLoadDefault();
      hydrateFromConfig(res?.config || {}, null);
      setSuccess(`Default tuning loaded (v${res?.version?.version_number || "-"}).`);
      await loadConfig();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to load default tuning");
    } finally {
      setLoadingDefault(false);
    }
  };

  const loadFromVersion = (version) => {
    const snapshot = version?.snapshot || {};
    hydrateFromConfig(snapshot, null);
    setSuccess(`Loaded version v${version?.version_number || "-"} into form.`);
  };

  const formatSectionLabel = (sectionKey) => {
    const section = SECTION_CONFIG.find((s) => s.key === sectionKey);
    return section ? section.title : "Global";
  };

  return (
    <DashboardContent maxWidth="xl">
      <Stack spacing={2}>
        <Box>
          <Typography variant="h4">Fine Tune the Brand Godfather AI engine</Typography>
          <Typography variant="body2" color="text.secondary">
            Configure phase prompts and train the selected BGF engine.
          </Typography>
        </Box>

        <Alert severity="info">
          Default System prompt Non editable. Other prompt fields are editable.
        </Alert>

        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}

        <Card sx={{ p: 3 }}>
          <Stack spacing={1.5}>
            <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1.5}>
              <Box>
                <Typography variant="h6">BGF Engine</Typography>
                <ToggleButtonGroup
                  exclusive
                  value={engine}
                  onChange={(_, nextValue) => {
                    if (!nextValue || hasBusySections) return;
                    setEngine(nextValue);
                  }}
                  size="small"
                >
                  <ToggleButton value="rag_v1">Use BGF engine1</ToggleButton>
                  <ToggleButton value="rag_v2">Use BGF engine2</ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <Box>
                <Button
                  variant="outlined"
                  onClick={loadDefault}
                  disabled={loadingDefault || hasBusySections}
                >
                  {loadingDefault ? "Loading default..." : "Load Default"}
                </Button>
              </Box>
            </Stack>

            {defaultTemplate ? (
              <Typography variant="caption" color="text.secondary">
                Default template version: v{defaultTemplate.version_number}
              </Typography>
            ) : null}
          </Stack>
        </Card>

        {loading ? (
          <Card sx={{ p: 4, display: "flex", justifyContent: "center" }}>
            <CircularProgress />
          </Card>
        ) : (
          SECTION_CONFIG.map((section) => {
            const sectionState = sections[section.key] || emptySectionState();
            const saving = !!savingBySection[section.key];
            const training = !!trainingBySection[section.key];

            return (
              <Card key={section.key} sx={{ p: 3 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">
                    {section.id}. {section.title}
                  </Typography>

                  <TextField
                    fullWidth
                    multiline
                    minRows={4}
                    label={
                      section.key === "phase_1_master_prompt"
                        ? "Optional Injection Prompt"
                        : "Input Prompt"
                    }
                    value={sectionState.prompt}
                    onChange={(e) =>
                      updateSectionField(section.key, "prompt", e.target.value)
                    }
                  />

                  <TextField
                    fullWidth
                    multiline
                    minRows={3}
                    label={
                      section.key === "phase_1_master_prompt"
                        ? "Optional Injection Goal"
                        : "Goal of Prompt"
                    }
                    value={sectionState.goal}
                    onChange={(e) =>
                      updateSectionField(section.key, "goal", e.target.value)
                    }
                  />

                  <TextField
                    fullWidth
                    multiline
                    minRows={3}
                    label={
                      section.key === "phase_1_master_prompt"
                        ? "Optional Injection Evaluation Criteria"
                        : "Evaluation Criteria of Prompt"
                    }
                    value={sectionState.criteria}
                    onChange={(e) =>
                      updateSectionField(section.key, "criteria", e.target.value)
                    }
                  />

                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                    <Button
                      variant="outlined"
                      onClick={() => saveSection(section.key)}
                      disabled={saving || training}
                    >
                      {saving ? "Saving..." : "Save"}
                    </Button>
                    <Button
                      variant="contained"
                      onClick={() => trainSection(section.key)}
                      disabled={saving || training}
                    >
                      {training ? "Training..." : "Train AI"}
                    </Button>
                  </Stack>

                  {section.key === "phase_1_master_prompt" ? (
                    <Accordion>
                      <AccordionSummary expandIcon={<Typography variant="body2">+</Typography>}>
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                          <Typography variant="body1">Mandatory Base Prompt</Typography>
                          <Chip size="small" color="warning" label="Default Non editable" />
                        </Stack>
                      </AccordionSummary>
                      <AccordionDetails>
                        <TextField
                          fullWidth
                          multiline
                          minRows={8}
                          label="Mandatory Base Prompt (BrandDiscoveryPrompt.md from DB)"
                          value={sectionState.mandatory_prompt || ""}
                          InputProps={{ readOnly: true }}
                          helperText="This base prompt is mandatory and locked."
                        />
                      </AccordionDetails>
                    </Accordion>
                  ) : null}
                </Stack>
              </Card>
            );
          })
        )}

        <Card sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h6">Past Fine Tunings (from DB)</Typography>

            {versions.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No version history found yet.
              </Typography>
            ) : (
              versions.map((version) => {
                const isOpen = expandedVersionId === version.id;
                return (
                  <Card key={version.id} variant="outlined" sx={{ p: 2 }}>
                    <Stack spacing={1.5}>
                      <Stack
                        direction={{ xs: "column", sm: "row" }}
                        justifyContent="space-between"
                        spacing={1}
                      >
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                          <Chip size="small" label={`v${version.version_number}`} />
                          <Chip size="small" label={version.action} />
                          <Chip size="small" label={formatSectionLabel(version.section_key)} />
                          <Chip
                            size="small"
                            label={version.active_pipeline === "rag_v2" ? "BGF engine2" : "BGF engine1"}
                          />
                        </Stack>

                        <Typography variant="caption" color="text.secondary">
                          {version.created_at ? new Date(version.created_at).toLocaleString() : "-"}
                        </Typography>
                      </Stack>

                      <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                        <Button variant="outlined" size="small" onClick={() => loadFromVersion(version)}>
                          Load This Version
                        </Button>
                        <Button
                          variant="text"
                          size="small"
                          onClick={() => setExpandedVersionId((prev) => (prev === version.id ? null : version.id))}
                        >
                          {isOpen ? "Hide Full Data" : "View Full Data"}
                        </Button>
                      </Stack>

                      {isOpen ? (
                        <TextField
                          fullWidth
                          multiline
                          minRows={8}
                          value={JSON.stringify(version.snapshot || {}, null, 2)}
                          InputProps={{ readOnly: true }}
                        />
                      ) : null}
                    </Stack>
                  </Card>
                );
              })
            )}
          </Stack>
        </Card>
      </Stack>
    </DashboardContent>
  );
}