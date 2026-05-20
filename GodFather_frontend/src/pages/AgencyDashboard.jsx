import React, { useEffect, useState } from "react";
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
} from "lucide-react";

// ── Sidebar Menu Items ──
const SIDEBAR_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: BarChart3 },
  { key: "clients", label: "Assigned Clients", icon: Users },
  { key: "sessions", label: "Active Sessions", icon: FolderOpen },
  { key: "review", label: "Review Queue", icon: ClipboardCheck },
  { key: "ai-insights", label: "AI Insights", icon: AlertTriangle },
  { key: "manifestos", label: "Manifestos", icon: FileText },
  { key: "feedback", label: "Comments & Feedback", icon: MessageSquare },
  { key: "unlock", label: "Brand Unlock Requests", icon: Unlock },
  { key: "analytics", label: "Analytics", icon: TrendingUp },
  { key: "notifications", label: "Notifications", icon: Bell },
  { key: "settings", label: "Profile & Team", icon: Settings },
];

// ── Sidebar ──
function Sidebar({ activeTab, onTabChange }) {
  return (
    <aside className="agency-sidebar">
      <div className="agency-sidebar-inner">
        <div className="agency-sidebar-header">
          <div className="agency-sidebar-label-row">
            <Menu size={18} className="agency-sidebar-menu-icon" />
            <span className="agency-sidebar-label">Menu</span>
          </div>
          <h3 className="agency-sidebar-title">Agency Panel</h3>
        </div>

        <nav className="agency-sidebar-nav">
          {SIDEBAR_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`agency-sidebar-item ${activeTab === item.key ? "active" : ""}`}
                onClick={() => onTabChange(item.key)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}

// ── Stats Card ──
function StatsCard({ title, value, icon: Icon, color }) {
  return (
    <div className="agency-stat-card">
      <div className="agency-stat-content">
        <p className="agency-stat-title">{title}</p>
        <h2 className="agency-stat-value">{value}</h2>
      </div>
      <div className="agency-stat-icon-wrap" style={{ background: color }}>
        <Icon size={24} color="#fff" />
      </div>
    </div>
  );
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
function SessionsTable({ sessions, onOpenSession }) {
  const getStatusDot = (status) =>
    String(status ?? "").toLowerCase().includes("complete") ? "completed" : "progress";

  return (
    <div className="agency-section-card">
      <h3 className="agency-section-heading">
        <FolderOpen size={20} /> All Sessions
      </h3>
      <div className="adb-table-container">
        <div className="adb-table-wrapper">
          <table className="adb-table" role="table">
            <thead>
              <tr>
                <th>Sr.No.</th>
                <th>Client Name</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Brand Stage</th>
                <th style={{ width: "160px", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session, index) => (
                <tr key={session.id ?? index}>
                  <td className="adb-td-index">{index + 1}</td>
                  <td className="adb-td-name">{session.title ?? session.name}</td>
                  <td>
                    <div className="adb-status">
                      <span className={`adb-dot ${getStatusDot(session.status)}`} />
                      <span className="adb-status-text">{session.status || "Draft"}</span>
                    </div>
                  </td>
                  <td>
                    <div className="agency-mini-progress">
                      <div
                        className="agency-mini-progress-fill"
                        style={{ width: `${session.progress ?? 0}%` }}
                      />
                      <span>{Math.round(session.progress ?? 0)}%</span>
                    </div>
                  </td>
                  <td className="adb-td-stage">{session.stage ?? "Foundation"}</td>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchDashboard() {
      setLoading(true);
      setError("");
      try {
        const data = await authService.getAgencyDashboard();
        if (!cancelled) setDashboardData(data);
      } catch (err) {
        if (!cancelled) setError(err?.message || "Failed to load dashboard");
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
    { title: "Assigned Clients", value: stats.assigned_clients ?? 0, icon: Users, color: "rgba(57, 89, 229, 0.8)" },
    { title: "In Progress Projects", value: stats.in_progress_projects ?? 0, icon: FolderOpen, color: "rgba(255, 195, 134, 0.8)" },
    { title: "Pending Reviews", value: stats.pending_reviews ?? 0, icon: ClipboardCheck, color: "rgba(142, 229, 255, 0.8)" },
    { title: "Approved Manifestos", value: stats.approved_manifestos ?? 0, icon: FileText, color: "rgba(134, 227, 100, 0.8)" },
    { title: "Weak AI Sessions", value: stats.weak_ai_sessions ?? 0, icon: AlertTriangle, color: "rgba(255, 107, 107, 0.8)" },
    { title: "Avg Brand Score", value: `${stats.avg_brand_score ?? 0}%`, icon: Star, color: "rgba(168, 130, 255, 0.8)" },
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
          <>
            <div className="agency-stats-grid">
              {statCards.map((s) => (
                <StatsCard key={s.title} {...s} />
              ))}
            </div>
            <div className="agency-two-col">
              <ReviewQueue items={dashboardData?.review_queue} onView={handleViewSession} />
              <AIAlerts alerts={dashboardData?.ai_alerts} />
            </div>
            <ClientProgress clients={dashboardData?.client_progress} />
            <RecentActivities activities={dashboardData?.recent_activities} />
          </>
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
      <ChatNavbar showDownloadButton={false} />
      <div className="adb-background">
        <div className="adb-glow-left" />
        <div className="adb-glow-right" />
      </div>
      <div className="adb-layout" style={{ height: "calc(100vh - 60px)" }}>
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
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
