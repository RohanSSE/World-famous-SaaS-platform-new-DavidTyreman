import { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { DashboardContent } from "@admin/layouts/dashboard/content";
import adminApi from "@admin/lib/adminApi";

function MetricCard({ label, value, ok }) {
  return (
    <Card sx={{ p: 2 }}>
      <Typography variant="overline" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5">{value ?? "—"}</Typography>
      {ok != null && (
        <Chip size="small" label={ok ? "OK" : "Watch"} color={ok ? "success" : "warning"} sx={{ mt: 1 }} />
      )}
    </Card>
  );
}

export default function CognitionDashboardPage() {
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [traces, setTraces] = useState([]);
  const [error, setError] = useState(null);

  const load = () => {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      setError("Log in via main app (superuser) so accessToken is in localStorage.");
      return;
    }
    Promise.all([
      adminApi.cognitionDashboard(7),
      adminApi.cognitionTraces(40),
      adminApi.cognitionLive(30),
    ])
      .then(([dash, tr, lv]) => {
        setData(dash);
        setTraces(tr.traces || []);
        setLive(lv);
      })
      .catch((e) => setError(e.response?.data?.detail || e.message || "Failed to load"));
  };

  useEffect(() => {
    load();
    const id = setInterval(() => {
      adminApi.cognitionLive(30).then(setLive).catch(() => {});
    }, 15000);
    return () => clearInterval(id);
  }, []);

  const obs = data?.observability;
  const cost = data?.cost;
  const signals = data?.product_signals;

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 2 }}>
        Cognition Observability
      </Typography>

      {error && <Alert severity="warning" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            label="Golden pass rate"
            value={obs ? `${obs.golden_passed}/${obs.golden_cases}` : "—"}
            ok={obs?.health?.find((h) => h.metric === "pass_rate")?.ok}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            label="Hallucination risk"
            value={obs?.metrics?.hallucination_risk}
            ok={obs?.health?.find((h) => h.metric === "hallucination_risk")?.ok}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            label="Avg latency (24h)"
            value={obs?.runtime_24h?.avg_latency_ms != null ? `${obs.runtime_24h.avg_latency_ms} ms` : "—"}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            label="Est. cost (period)"
            value={cost?.estimated_cost_usd != null ? `$${cost.estimated_cost_usd}` : "—"}
          />
        </Grid>
      </Grid>

      {live && (
        <Card sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Live cognition (30m) — auto-refresh 15s
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            <Chip label={`Requests: ${live.request_count}`} />
            <Chip label={`Unsupported est.: ${live.estimated_unsupported_claims}`} />
            <Chip label={`Repairs: ${live.repair_count}`} />
            <Chip label={`Low retrieval conf.: ${live.low_retrieval_confidence}`} />
            <Chip label={`Avg latency: ${live.avg_latency_ms}ms`} />
            <Chip label={`Exports: ${live.recent_exports}`} />
          </Box>
        </Card>
      )}

      {signals && (
        <Card sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6">Product signals ({signals.period_days}d)</Typography>
          <Typography variant="body2">
            Exports: {signals.export_count} | Feedback sessions: {signals.feedback_learning_sessions} | Active sessions: {signals.active_sessions}
          </Typography>
        </Card>
      )}

      {obs?.health?.length > 0 && (
        <Card sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Reliability targets
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {obs.health.map((h) => (
              <Chip
                key={h.metric}
                label={`${h.metric}: ${h.value} (target ${h.target})`}
                color={h.ok ? "success" : "default"}
                variant={h.ok ? "filled" : "outlined"}
              />
            ))}
          </Box>
        </Card>
      )}

      <Card sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          Recent AI request traces
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Session</TableCell>
              <TableCell>Pipeline</TableCell>
              <TableCell>Latency</TableCell>
              <TableCell>Hallucination</TableCell>
              <TableCell>Query</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {traces.map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.id}</TableCell>
                <TableCell>{t.session_id}</TableCell>
                <TableCell>{t.pipeline}</TableCell>
                <TableCell>{t.total_ms} ms</TableCell>
                <TableCell>{t.hallucination_risk ?? "—"}</TableCell>
                <TableCell sx={{ maxWidth: 280 }}>{t.query_preview}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </DashboardContent>
  );
}
