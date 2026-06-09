import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../components/AgencyDashboard.css";
import authService from "../services/authService";
import ChatNavbar from "./ChatNavbar";
import {
  Users,
  FolderOpen,
  ClipboardCheck,
  FileText,
  AlertTriangle,
  BarChart3,
  Menu,
  Search,
  Bell,
  Settings,
  MessageSquare,
  Unlock,
  TrendingUp,
  Eye,
  ChevronRight,
  Activity,
  Shield,
  Star,
  CreditCard,
} from "lucide-react";
import PaymentHistoryCard from "../components/PaymentHistoryCard";

// ── Sidebar Menu Items ──
const SIDEBAR_ITEMS = [
  { key: "dashboard", label: "Agency Dashboard", icon: BarChart3 },
  { key: "clients", label: "Start a Project", icon: FolderOpen },
];

// ── Sidebar ──
function Sidebar({ activeTab, onTabChange, collapsed, onToggleCollapse }) {
  return (
    <aside className={`agency-sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="agency-sidebar-inner">
        <div className="agency-sidebar-header">
          <div className="agency-sidebar-label-row">
            <button className="agency-sidebar-toggle" onClick={onToggleCollapse} title={collapsed ? "Expand menu" : "Collapse menu"}>
              <Menu size={18} />
            </button>
            {!collapsed && <span className="agency-sidebar-label">Menu</span>}
          </div>
          {!collapsed && <h3 className="agency-sidebar-title">Agency Panel</h3>}
        </div>

        <nav className="agency-sidebar-nav">
          {SIDEBAR_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`agency-sidebar-item ${activeTab === item.key ? "active" : ""}`}
                onClick={() => onTabChange(item.key)}
                title={collapsed ? item.label : ""}
              >
                <Icon size={18} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {!collapsed && (
          <div className="agency-sidebar-search" aria-label="Search">
            <Search size={10} />
            <span>Search</span>
          </div>
        )}
      </div>
    </aside>
  );
}

const AGENCY_CARD_ICONS = {
  totalClients: "/Agency_icon_completed_project.png",
  projectInProgress: "/Agency_icon_project_in_progress.png",
  completedProject: "/Agency_icon_total_clinet.png",
};

// ── Stats Card ──
function StatsCard({ title, value, imageSrc }) {
  return (
    <div className="agency-stat-card">
      <div className="agency-stat-content">
        <p className="agency-stat-title">{title}</p>
        <h2 className="agency-stat-value">{value}</h2>
      </div>
      <div className="agency-stat-icon-wrap">
        <img src={imageSrc} alt="" className="agency-stat-icon" aria-hidden="true" />
      </div>
    </div>
  );
}

function getSessionStatusLabel(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized.includes("complete") || normalized.includes("locked")) return "Completed";
  return "In Progress";
}

function getSessionBrandStage(session) {
  if (session?.current_stage_label) return session.current_stage_label;
  if (session?.stage) return session.stage;
  const statusLabel = getSessionStatusLabel(session?.status);
  if (statusLabel === "Completed") return "PDF Generated";
  const progress = Number(session?.progress ?? 0);
  if (progress >= 75) return "Brand Visual";
  if (progress >= 50) return "Brand Discipline";
  if (progress >= 25) return "Emotional Anchor";
  return "Foundation";
}

function getSessionStageProgress(session) {
  const stageProgress = Number(session?.stage_progress);
  if (Number.isFinite(stageProgress)) return Math.max(0, Math.min(stageProgress, 100));
  return Math.max(0, Math.min(Number(session?.progress ?? 0), 100));
}

function getSessionStageMeta(session) {
  const answered = Number(session?.stage_answered_questions ?? 0);
  const total = Number(session?.stage_total_questions ?? 0);
  if (total > 0) return `${answered}/${total} questions`;

  const completedStages = Number(session?.completed_stage_count ?? 0);
  const totalStages = Number(session?.total_stage_count ?? 0);
  if (totalStages > 0) return `${completedStages}/${totalStages} stages`;

  return `${Math.round(getSessionStageProgress(session))}% done`;
}

// ── Review Queue Section ──
function ReviewQueue({ items, onView }) {
  if (!items || items.length === 0) {
    return <p className="agency-empty">No items in review queue</p>;
  }
  return (
    <div className="agency-section-card">
      <h3 className="agency-section-heading">
        <ClipboardCheck size={20} /> Review Queue
      </h3>
      <div className="agency-queue-list">
        {items.map((item, i) => (
          <div key={i} className="agency-queue-item">
            <div className="agency-queue-left">
              <div className="agency-queue-avatar">
                {(item.client_name || "?")[0].toUpperCase()}
              </div>
              <div>
                <p className="agency-queue-name">{item.client_name}</p>
                <p className="agency-queue-email">{item.client_email}</p>
              </div>
            </div>
            <div className="agency-queue-right">
              <span className={`agency-badge ${item.status === "completed" ? "review" : "progress"}`}>
                {item.issue}
              </span>
              <button className="agency-btn-sm" onClick={() => onView(item)}>
                <Eye size={14} /> View
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── AI Alerts Section ──
function AIAlerts({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return null;
  }
  return (
    <div className="agency-section-card">
      <h3 className="agency-section-heading">
        <AlertTriangle size={20} /> AI Alerts
      </h3>
      <div className="agency-alerts-list">
        {alerts.map((alert, i) => (
          <div key={i} className={`agency-alert-item ${alert.severity}`}>
            <AlertTriangle size={16} />
            <div>
              <p className="agency-alert-text">{alert.alert}</p>
              <p className="agency-alert-client">{alert.client_name}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Client Progress Tracker ──
function ClientProgress({ clients }) {
  if (!clients || clients.length === 0) {
    return null;
  }

  const stageOrder = ["Basic", "Foundation", "Identity", "More", "Complete"];

  return (
    <div className="agency-section-card">
      <h3 className="agency-section-heading">
        <TrendingUp size={20} /> Client Progress Tracker
      </h3>
      <div className="agency-progress-list">
        {clients.map((client, i) => (
          <div key={i} className="agency-progress-item">
            <div className="agency-progress-header">
              <span className="agency-progress-name">{client.client_name}</span>
              <span className="agency-progress-pct">{client.progress}%</span>
            </div>
            <div className="agency-progress-bar-wrap">
              <div
                className="agency-progress-bar-fill"
                style={{ width: `${Math.min(client.progress, 100)}%` }}
              />
            </div>
            <div className="agency-progress-stages">
              {stageOrder.map((stage, idx) => (
                <span
                  key={idx}
                  className={`agency-stage-dot ${
                    client.current_stage === stage
                      ? "current"
                      : stageOrder.indexOf(client.current_stage) > idx
                      ? "done"
                      : ""
                  }`}
                >
                  {stage}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Recent Activities ──
function RecentActivities({ activities }) {
  if (!activities || activities.length === 0) {
    return null;
  }

  const getIcon = (type) => {
    switch (type) {
      case "answer_updated": return <Activity size={16} className="act-icon update" />;
      case "manifesto_generated": return <FileText size={16} className="act-icon manifesto" />;
      case "comment_added": return <MessageSquare size={16} className="act-icon comment" />;
      default: return <Activity size={16} className="act-icon" />;
    }
  };

  const formatTime = (ts) => {
    const d = new Date(ts);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return d.toLocaleDateString();
  };

  return (
    <div className="agency-section-card">
      <h3 className="agency-section-heading">
        <Activity size={20} /> Recent Activities
      </h3>
      <div className="agency-activity-list">
        {activities.map((act, i) => (
          <div key={i} className="agency-activity-item">
            {getIcon(act.type)}
            <div className="agency-activity-content">
              <p className="agency-activity-msg">{act.message}</p>
              <p className="agency-activity-time">{formatTime(act.timestamp)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sessions Table ──
function SessionsTable({ sessions = [], onOpenSession, heading = "All Sessions", showProgress = true, limit }) {
  const [searchQuery, setSearchQuery] = useState("");
  const getStatusDot = (status) =>
    getSessionStatusLabel(status) === "Completed" ? "completed" : "progress";
  const filteredRows = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return sessions;

    return sessions.filter((session) => {
      const searchable = [
        session.title,
        session.name,
        session.created_by_email,
        getSessionStatusLabel(session.status),
        getSessionBrandStage(session),
        getSessionStageMeta(session),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchable.includes(query);
    });
  }, [searchQuery, sessions]);
  const rows = typeof limit === "number" ? filteredRows.slice(0, limit) : filteredRows;

  return (
    <div className={`agency-section-card ${!heading ? "agency-dashboard-table-card" : ""}`}>
      {heading && (
        <h3 className="agency-section-heading">
          <FolderOpen size={20} /> {heading}
        </h3>
      )}
      <div className="agency-table-toolbar">
        <div className="agency-table-search">
          <Search size={14} />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search client, status, or stage"
            aria-label="Search client projects"
          />
        </div>
        <span className="agency-table-count">
          {rows.length} of {sessions.length} clients
        </span>
      </div>
      <div className="adb-table-container">
        <div className="adb-table-wrapper">
          <table className="adb-table" role="table">
            <thead>
              <tr>
                <th>Sr.No.</th>
                <th>Client Name</th>
                <th>Status</th>
                <th>Brand Stage</th>
                {showProgress && <th>Progress</th>}
                <th style={{ width: "160px", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={showProgress ? 6 : 5} className="adb-empty-row">
                    No client projects found
                  </td>
                </tr>
              )}
              {rows.map((session, index) => (
                <tr key={session.id ?? index}>
                  <td className="adb-td-index">{index + 1}</td>
                  <td className="adb-td-name">{session.title ?? session.name}</td>
                  <td>
                    <div className="adb-status">
                      <span className={`adb-dot ${getStatusDot(session.status)}`} />
                      <span className="adb-status-text">{getSessionStatusLabel(session.status)}</span>
                    </div>
                  </td>
                  <td className="adb-td-stage">
                    <div className="agency-stage-cell">
                      <div className="agency-stage-line">
                        <span>{getSessionBrandStage(session)}</span>
                        <strong>{Math.round(getSessionStageProgress(session))}%</strong>
                      </div>
                      <div className="agency-stage-progress-track">
                        <div
                          className="agency-stage-progress-fill"
                          style={{ width: `${getSessionStageProgress(session)}%` }}
                        />
                      </div>
                      <span className="agency-stage-meta">{getSessionStageMeta(session)}</span>
                    </div>
                  </td>
                  {showProgress && <td>
                    <div className="agency-mini-progress">
                      <div
                        className="agency-mini-progress-fill"
                        style={{ width: `${session.progress ?? 0}%` }}
                      />
                      <span>{Math.round(session.progress ?? 0)}%</span>
                    </div>
                  </td>}
                  <td className="adb-td-action">
                    <button
                      className="adb-btn-view"
                      onClick={() => {
                        localStorage.setItem("session", JSON.stringify(session));
                        if (session.id) localStorage.setItem("sessionId", session.id);
                        if (onOpenSession) onOpenSession(session);
                      }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Main Agency Dashboard ──
export default function AgencyDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchDashboard() {
      setLoading(true);
      setError("");
      try {
        const currentUser = authService.getCurrentUser() || {};
        const isAgencyUser = currentUser.role === 3 || currentUser.role_name === "agency";
        if (isAgencyUser) {
          const redirect = await authService.getAgencyOnboardingRedirect();
          if (redirect.route !== "/agency-dashboard") {
            navigate(redirect.route, { replace: true });
            return;
          }
        }
        const data = await authService.getAgencyDashboard();
        if (!cancelled) setDashboardData(data);
      } catch (err) {
        if (!cancelled) {
          const msg = err?.message || err?.detail || "Failed to load dashboard";
          const isPending =
            err?.status === 403 ||
            err?.code === "agency_pending_approval" ||
            String(msg).toLowerCase().includes("pending");
          if (isPending) {
            navigate("/agency-pending", { replace: true });
            return;
          }
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchDashboard();
    return () => { cancelled = true; };
  }, []);

  const stats = dashboardData?.stats || {};
  const sessions = dashboardData?.sessions || [];

  const statCards = [
    {
      title: "Total Clients",
      value: stats.assigned_clients ?? sessions.length,
      imageSrc: AGENCY_CARD_ICONS.totalClients,
    },
    {
      title: "Project in Progress",
      value: stats.in_progress_projects ?? sessions.filter((s) => getSessionStatusLabel(s.status) === "In Progress").length,
      imageSrc: AGENCY_CARD_ICONS.projectInProgress,
    },
    {
      title: "Completed Project",
      value: stats.completed_projects ?? stats.pending_reviews ?? sessions.filter((s) => getSessionStatusLabel(s.status) === "Completed").length,
      imageSrc: AGENCY_CARD_ICONS.completedProject,
    },
  ];

  const handleViewSession = (item) => {
    const session = sessions.find((s) => s.id === item.session_id) || item;
    localStorage.setItem("session", JSON.stringify(session));
    if (session.id) localStorage.setItem("sessionId", session.id);
    navigate("/manifesto");
  };

  // ── Render content based on active tab ──
  const renderContent = () => {
    if (loading) {
      return <div className="agency-loading">Loading agency dashboard...</div>;
    }
    if (error) {
      return <div className="agency-error">Error: {error}</div>;
    }

    switch (activeTab) {
      case "dashboard":
        return (
          <div className="agency-dashboard-overview">
            <div className="agency-stats-grid">
              {statCards.map((s) => (
                <StatsCard key={s.title} {...s} />
              ))}
            </div>
            <SessionsTable
              sessions={sessions}
              onOpenSession={() => navigate("/manifesto")}
              heading={null}
              showProgress={false}
            />
          </div>
        );
      case "clients":
        return (
          <>
            <h2 className="agency-tab-title">Assigned Clients</h2>
            <SessionsTable sessions={sessions} onOpenSession={() => navigate("/manifesto")} />
          </>
        );
      case "sessions":
        return (
          <>
            <h2 className="agency-tab-title">Active Sessions</h2>
            <SessionsTable
              sessions={sessions.filter((s) => s.status === "in_progress")}
              onOpenSession={() => navigate("/manifesto")}
            />
          </>
        );
      case "review":
        return (
          <>
            <h2 className="agency-tab-title">Review Queue</h2>
            <ReviewQueue items={dashboardData?.review_queue} onView={handleViewSession} />
          </>
        );
      case "ai-insights":
        return (
          <>
            <h2 className="agency-tab-title">AI Insights</h2>
            <AIAlerts alerts={dashboardData?.ai_alerts} />
            <ClientProgress clients={dashboardData?.client_progress} />
          </>
        );
      case "manifestos":
        return (
          <>
            <h2 className="agency-tab-title">Manifestos</h2>
            <SessionsTable
              sessions={sessions.filter((s) => s.status === "completed" || s.status === "locked")}
              onOpenSession={() => navigate("/manifesto")}
            />
          </>
        );
      case "feedback":
        return (
          <>
            <h2 className="agency-tab-title">Comments & Feedback</h2>
            <RecentActivities
              activities={(dashboardData?.recent_activities || []).filter(
                (a) => a.type === "comment_added"
              )}
            />
          </>
        );
      case "analytics":
        return (
          <>
            <h2 className="agency-tab-title">Analytics</h2>
            <div className="agency-stats-grid">
              {statCards.map((s) => (
                <StatsCard key={s.title} {...s} />
              ))}
            </div>
            <ClientProgress clients={dashboardData?.client_progress} />
          </>
        );
      case "notifications":
        return (
          <>
            <h2 className="agency-tab-title">Notifications</h2>
            <RecentActivities activities={dashboardData?.recent_activities} />
          </>
        );
      case "billing":
        return (
          <>
            <h2 className="agency-tab-title">Billing & Invoices</h2>
            <PaymentHistoryCard />
          </>
        );
      default:
        return (
          <div className="agency-placeholder">
            <Shield size={48} />
            <p>This section is coming soon.</p>
          </div>
        );
    }
  };

  return (
    <div className="adb-root" style={{ overflow: "hidden", height: "100vh" }}>
      <ChatNavbar showSaveButton={false} showDownloadButton={false} showLogoutButton={true} />
      <div className="adb-background">
        <div className="adb-glow-left" />
        <div className="adb-glow-right" />
      </div>
      <div className="adb-layout" style={{ height: "calc(100vh - 45px)" }}>
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} collapsed={sidebarCollapsed} onToggleCollapse={() => setSidebarCollapsed(c => !c)} />
        <main className="adb-main-content">
          <div className="adb-content-wrapper">
            <h1 className="adb-page-title">Agency Dashboard</h1>
            <div className="agency-bg-animate">
              <div className="bg-glow gl-1"></div>
              <div className="bg-glow gl-2"></div>
              <div className="bg-glow gl-3"></div>
              {renderContent()}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
