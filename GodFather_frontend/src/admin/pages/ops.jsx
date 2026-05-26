import { useEffect, useState } from "react";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import Alert from "@mui/material/Alert";
import Chip from "@mui/material/Chip";
import Box from "@mui/material/Box";
import { DashboardContent } from "@admin/layouts/dashboard/content";
import adminApi from "@admin/lib/adminApi";

export default function OpsIntelligencePage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    adminApi
      .opsIntelligence(14)
      .then(setData)
      .catch((e) => setError(e.response?.data?.detail || e.message));
  }, []);

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 2 }}>
        AI Operations
      </Typography>
      {error && <Alert severity="warning">{error}</Alert>}
      {data && (
        <>
          <Card sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6">Chunk quality</Typography>
            <Typography variant="body2">
              Weak: {data.chunk_audit_summary?.weak} | Generic: {data.chunk_audit_summary?.generic} |
              Duplicates: {data.chunk_audit_summary?.duplicates}
            </Typography>
            <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 0.5 }}>
              {(data.weak_chunk_alerts || []).map((c) => (
                <Chip key={c.chunk_id} size="small" label={`#${c.chunk_id} ${c.title?.slice(0, 20)}`} />
              ))}
            </Box>
          </Card>
          <Card sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6">High repair sessions</Typography>
            {(data.high_repair_sessions || []).map((s) => (
              <Typography key={s.session_id} variant="body2">
                Session {s.session_id}: {s.repairs} repairs, {s.requests} requests
              </Typography>
            ))}
          </Card>
          <Card sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6">Workflows needing attention</Typography>
            {(data.workflows_needing_attention || []).map((w, i) => (
              <Typography key={i} variant="body2">
                {w.pipeline || w.agent_id}: {w.c} high-risk (avg hall {Number(w.avg_hall || 0).toFixed(2)})
              </Typography>
            ))}
          </Card>
          <Card sx={{ p: 2 }}>
            <Typography variant="h6">Most edited outputs (feedback learning)</Typography>
            {(data.most_edited_outputs || []).map((o) => (
              <Typography key={o.session_id} variant="body2">
                Session {o.session_id} — edits {o.edit_count}, rejected: {(o.rejected_phrases || []).join(", ")}
              </Typography>
            ))}
          </Card>
        </>
      )}
    </DashboardContent>
  );
}
