import { useEffect, useState, useMemo } from "react";
import { Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Grid from "@mui/material/Grid";
import Alert from "@mui/material/Alert";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Button from "@mui/material/Button";
import { Iconify } from "@admin/components/iconify";
import { DashboardContent } from "@admin/layouts/dashboard";
import { AnalyticsCurrentVisits } from "../analytics-current-visits";
import adminApi from "@admin/lib/adminApi";

function StatCard({ title, value, subtitle, icon, color = "#4a6cf7" }) {
  return (
    <Card
      className="admin-stat-card"
      sx={{
        p: 2.5,
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(26, 28, 58, 0.55)",
        border: "1.5px solid #5b6798",
        borderRadius: "16px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
      }}
    >
      <Box>
        <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.6)", mb: 0.5 }}>
          {title}
        </Typography>
        <Typography variant="h4" sx={{ color: "#fff", fontWeight: 600, lineHeight: 1.1 }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.45)", mt: 0.5, display: "block" }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      <Box
        sx={{
          width: 52,
          height: 52,
          borderRadius: "12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: `linear-gradient(135deg, ${color}33, ${color}18)`,
          color,
          flexShrink: 0,
        }}
      >
        <Iconify icon={icon} width={28} />
      </Box>
    </Card>
  );
}

function QuickLinkCard({ title, description, href, icon }) {
  return (
    <Card
      component={RouterLink}
      to={href}
      sx={{
        p: 2,
        textDecoration: "none",
        display: "block",
        background: "rgba(26, 28, 58, 0.4)",
        border: "1px solid rgba(142, 229, 255, 0.1)",
        borderRadius: "12px",
        transition: "border-color 0.2s, background 0.2s",
        "&:hover": {
          borderColor: "rgba(86, 227, 255, 0.35)",
          background: "rgba(57, 89, 229, 0.12)",
        },
      }}
    >
      <Box sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
        <Iconify icon={icon} width={22} sx={{ color: "#86e3ff", mt: 0.25 }} />
        <Box>
          <Typography variant="subtitle2" sx={{ color: "#fff" }}>
            {title}
          </Typography>
          <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.55)" }}>
            {description}
          </Typography>
        </Box>
      </Box>
    </Card>
  );
}

function roleKey(u) {
  return (u.role_name || "").toLowerCase();
}

function AdminDashboardView() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [users, setUsers] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [obs, setObs] = useState(null);
  const [feedbackItems, setFeedbackItems] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      const results = await Promise.allSettled([
        adminApi.listUsers(),
        adminApi.listAgencies(),
        adminApi.productObservability(),
        adminApi.feedbackReview(100),
        adminApi.listSessions(),
      ]);

      if (cancelled) return;

      const [uRes, aRes, oRes, fRes, sRes] = results;

      if (uRes.status === "fulfilled") {
        setUsers(Array.isArray(uRes.value) ? uRes.value : uRes.value?.results || []);
      }
      if (aRes.status === "fulfilled") {
        setAgencies(Array.isArray(aRes.value) ? aRes.value : aRes.value?.results || []);
      }
      if (oRes.status === "fulfilled") setObs(oRes.value);
      if (fRes.status === "fulfilled") setFeedbackItems(fRes.value?.items || []);
      if (sRes.status === "fulfilled") {
        setSessions(Array.isArray(sRes.value) ? sRes.value : []);
      }

      const failed = [uRes, aRes].filter((r) => r.status === "rejected");
      if (failed.length) {
        const msg =
          failed[0].reason?.response?.data?.detail ||
          failed[0].reason?.message ||
          "Failed to load dashboard";
        setError(typeof msg === "string" ? msg : "Failed to load dashboard");
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = useMemo(() => {
    const activeUsers = users.filter((u) => u.is_active).length;
    const clientUsers = users.filter((u) => roleKey(u) === "client").length;
    const agencyUsers = users.filter((u) => roleKey(u) === "agency").length;
    const activeAgencies = agencies.filter((a) => a.is_active).length;

    const sessionByStatus = { draft: 0, in_progress: 0, completed: 0, locked: 0, other: 0 };
    sessions.forEach((s) => {
      const st = s.status || "other";
      if (sessionByStatus[st] !== undefined) sessionByStatus[st] += 1;
      else sessionByStatus.other += 1;
    });

    const runtime = obs?.runtime_24h || {};
    const golden = obs?.golden_cases
      ? `${obs.golden_passed ?? 0}/${obs.golden_cases}`
      : "—";

    return {
      totalUsers: users.length,
      activeUsers,
      clientUsers,
      agencyUsers,
      totalAgencies: agencies.length,
      activeAgencies,
      totalSessions: sessions.length,
      inProgressSessions: sessionByStatus.in_progress,
      completedSessions: sessionByStatus.completed,
      aiRequests24h: runtime.total_traces_24h ?? "—",
      golden,
      pendingReview: feedbackItems.length,
      sessionByStatus,
    };
  }, [users, agencies, sessions, obs, feedbackItems]);

  const userRoleChart = useMemo(() => {
    const client = users.filter((u) => roleKey(u) === "client").length;
    const agency = users.filter((u) => roleKey(u) === "agency").length;
    const admin = users.filter((u) => roleKey(u) === "admin" || u.is_superuser).length;
    const other = users.length - client - agency - admin;
    return {
      series: [
        { label: "Brand users", value: client },
        { label: "Agency accounts", value: agency },
        { label: "Admins", value: admin },
        ...(other > 0 ? [{ label: "Other", value: other }] : []),
      ].filter((x) => x.value > 0),
    };
  }, [users]);

  const sessionChart = useMemo(() => {
    const { draft, in_progress, completed, locked } = stats.sessionByStatus;
    return {
      series: [
        { label: "In progress", value: in_progress },
        { label: "Completed", value: completed },
        { label: "Draft", value: draft },
        { label: "Locked", value: locked },
      ].filter((x) => x.value > 0),
    };
  }, [stats.sessionByStatus]);

  if (loading) {
    return (
      <DashboardContent>
        <Box sx={{ py: 10, display: "flex", justifyContent: "center" }}>
          <CircularProgress sx={{ color: "#86e3ff" }} />
        </Box>
      </DashboardContent>
    );
  }

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" className="adb-page-title" sx={{ mb: 1 }}>
        Admin Dashboard
      </Typography>
      <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.6)", mb: 3 }}>
        Brand Godfather platform overview — users, agencies, brand sessions & AI health
      </Typography>

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Total users"
            value={stats.totalUsers}
            subtitle={`${stats.activeUsers} active`}
            icon="solar:users-group-rounded-bold"
            color="#4a6cf7"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Brand users"
            value={stats.clientUsers}
            subtitle="Client role"
            icon="solar:user-rounded-bold"
            color="#507fec"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Agencies"
            value={stats.totalAgencies}
            subtitle={`${stats.activeAgencies} active · ${stats.agencyUsers} accounts`}
            icon="solar:buildings-2-bold"
            color="#86e3ff"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Brand sessions"
            value={stats.totalSessions}
            subtitle={`${stats.inProgressSessions} in progress`}
            icon="solar:document-text-bold"
            color="#6b5cff"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Pending review"
            value={stats.pendingReview}
            subtitle="Feedback & exports"
            icon="solar:clipboard-check-bold"
            color="#ffc386"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="AI requests (24h)"
            value={stats.aiRequests24h}
            subtitle="Cognition traces"
            icon="solar:cpu-bolt-bold"
            color="#22c55e"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Completed sessions"
            value={stats.completedSessions}
            subtitle="Ready for agency review"
            icon="solar:check-circle-bold"
            color="#8b5cf6"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <StatCard
            title="Golden eval"
            value={stats.golden}
            subtitle="Baseline pass rate"
            icon="solar:shield-check-bold"
            color="#3959e5"
          />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          {userRoleChart.series.length > 0 ? (
            <AnalyticsCurrentVisits title="Users by role" chart={userRoleChart} />
          ) : (
            <Card sx={{ p: 3 }}>
              <Typography color="text.secondary">No users yet</Typography>
            </Card>
          )}
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          {sessionChart.series.length > 0 ? (
            <AnalyticsCurrentVisits title="Sessions by status" chart={sessionChart} />
          ) : (
            <Card sx={{ p: 3 }}>
              <Typography color="text.secondary">No brand sessions yet</Typography>
            </Card>
          )}
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ color: "#fff", mb: 1.5 }}>
        Quick actions
      </Typography>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <QuickLinkCard
            title="Users & Agencies"
            description="Manage accounts, activate or deactivate"
            href="/admin/user"
            icon="solar:users-group-rounded-bold"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <QuickLinkCard
            title="Cognition"
            description="AI quality, traces & golden metrics"
            href="/admin/cognition"
            icon="solar:chart-2-bold"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <QuickLinkCard
            title="Review queue"
            description="Feedback and export review"
            href="/admin/review"
            icon="solar:clipboard-list-bold"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <QuickLinkCard
            title="AI Operations"
            description="Chunk quality & workflow alerts"
            href="/admin/ops"
            icon="solar:settings-bold"
          />
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: "flex", gap: 1, flexWrap: "wrap" }}>
        <Button component={RouterLink} to="/admin/user" variant="contained" color="primary">
          Manage users
        </Button>
        <Button component={RouterLink} to="/admin/cognition" variant="outlined" sx={{ borderColor: "#5b6798", color: "#86e3ff" }}>
          View cognition
        </Button>
      </Box>
    </DashboardContent>
  );
}

export { AdminDashboardView };
