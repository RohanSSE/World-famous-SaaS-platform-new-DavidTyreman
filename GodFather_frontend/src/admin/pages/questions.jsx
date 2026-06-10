import { useEffect, useMemo, useState } from "react";
import Card from "@mui/material/Card";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import TextField from "@mui/material/TextField";
import Stack from "@mui/material/Stack";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";

import adminApi from "@admin/lib/adminApi";
import { DashboardContent } from "@admin/layouts/dashboard/content";

const STAGE_CONFIG = [
  { stage: 1, label: "Phase 1 (8 questions)", count: 8 },
  { stage: 2, label: "Phase 2 (12 questions)", count: 12 },
  { stage: 3, label: "Phase 3 (10 questions)", count: 10 },
];

function emptyTextsByStage() {
  return STAGE_CONFIG.reduce((acc, s) => {
    acc[s.stage] = Array.from({ length: s.count }, () => "");
    return acc;
  }, {});
}

export default function AdminQuestionsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [textsByStage, setTextsByStage] = useState(() => emptyTextsByStage());
  const [expandedStage, setExpandedStage] = useState(1);

  const stageMap = useMemo(
    () => STAGE_CONFIG.reduce((acc, s) => ({ ...acc, [s.stage]: s }), {}),
    []
  );

  const loadQuestions = async () => {
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const list = await adminApi.listQuestions();
      const next = emptyTextsByStage();

      for (const cfg of STAGE_CONFIG) {
        const items = (Array.isArray(list) ? list : [])
          .filter((q) => String(q.stage) === String(cfg.stage))
          .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

        for (let i = 0; i < cfg.count; i += 1) {
          next[cfg.stage][i] = items[i]?.text ?? "";
        }
      }

      setTextsByStage(next);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTextChange = (stage, idx, value) => {
    setTextsByStage((prev) => {
      const copy = { ...prev };
      copy[stage] = [...prev[stage]];
      copy[stage][idx] = value;
      return copy;
    });
  };

  const validate = () => {
    for (const cfg of STAGE_CONFIG) {
      const arr = textsByStage[cfg.stage] || [];
      if (arr.length !== cfg.count) {
        return `Stage ${cfg.stage} must have exactly ${cfg.count} items.`;
      }
      for (let i = 0; i < cfg.count; i += 1) {
        const t = String(arr[i] ?? "").trim();
        if (!t) return `Stage ${cfg.stage} question #${i + 1} cannot be empty.`;
      }
    }
    return "";
  };

  const handleSave = async () => {
    const msg = validate();
    if (msg) {
      setError(msg);
      setSuccess("");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const payload = {
        stages: {
          1: textsByStage[1].map((t) => String(t).trim()),
          2: textsByStage[2].map((t) => String(t).trim()),
          3: textsByStage[3].map((t) => String(t).trim()),
        },
      };

      await adminApi.bulkSetQuestions(payload);
      setSuccess("Questions updated successfully.");
      await loadQuestions();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Failed to update questions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardContent maxWidth="xl">
      <Stack spacing={2}>
        <Typography variant="h4">Questions Manager</Typography>
        <Typography variant="body2" color="text.secondary">
          Admin sets source question texts per stage. Users and agencies see AI-refined versions in their Phase pages.
        </Typography>

        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}

        <Card sx={{ p: 2 }}>
          <Stack spacing={2}>
            {STAGE_CONFIG.map((cfg) => {
              const isOpen = expandedStage === cfg.stage;
              return (
                <Accordion
                  key={cfg.stage}
                  expanded={isOpen}
                  onChange={() => setExpandedStage((prev) => (prev === cfg.stage ? 0 : cfg.stage))}
                  sx={{
                    backgroundColor: "rgba(255,255,255,0.02)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    "&:before": { display: "none" },
                  }}
                >
                  <AccordionSummary
                    expandIcon={<span style={{ fontSize: 18, lineHeight: 1 }}>▾</span>}
                    sx={{ "& .MuiAccordionSummary-content": { m: 0 } }}
                  >
                    <Typography variant="subtitle1" fontWeight={700}>
                      {cfg.label}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack spacing={2}>
                      {Array.from({ length: cfg.count }).map((_, idx) => (
                        <TextField
                          key={`${cfg.stage}-${idx}`}
                          fullWidth
                          variant="outlined"
                          label={`Q${idx + 1}`}
                          value={textsByStage[cfg.stage]?.[idx] ?? ""}
                          multiline
                          minRows={2}
                          InputLabelProps={{ shrink: true }}
                          onChange={(e) =>
                            handleTextChange(cfg.stage, idx, e.target.value)
                          }
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              backgroundColor: "rgba(255,255,255,0.03)",
                            },
                          }}
                        />
                      ))}
                    </Stack>
                  </AccordionDetails>
                </Accordion>
              );
            })}
          </Stack>
        </Card>

        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button variant="contained" onClick={handleSave} disabled={loading}>
            {loading ? "Saving..." : "Save Questions"}
          </Button>
        </Stack>
      </Stack>
    </DashboardContent>
  );
}

