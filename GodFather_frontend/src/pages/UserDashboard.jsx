import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../components/UserDashboard.css";
import ChatNavbar from "../pages/ChatNavbar";
import { toast } from "react-toastify";
import {
  Plus,
  Search,
  Menu,
  BarChart3,
  FolderOpen,
  Layers,
  MessageCircle,
  Compass,
  FileUp,
  Sparkles,
  FileText,
  Share2,
  MessageSquare,
  Bell,
  Settings,
  ArrowRight,
  Activity,
  AlertTriangle,
  TrendingUp,
  Download,
  Edit3,
  Star,
  CheckCircle,
} from "lucide-react";
import authService from "../services/authService";
import CommentsModal from "./CommentsModal";

// ── Sidebar Menu Items ──
const USER_SIDEBAR_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: BarChart3 },
  { key: "sessions", label: "My Projects / Sessions", icon: FolderOpen },
  { key: "foundation", label: "Foundation Questions", icon: Layers },
  { key: "discovery", label: "Brand Discovery Chat", icon: MessageCircle },
  { key: "deepdive", label: "Deep Dive", icon: Compass },
  { key: "documents", label: "Documents", icon: FileUp },
  { key: "ai-suggestions", label: "AI Suggestions", icon: Sparkles },
  { key: "manifesto", label: "Manifesto", icon: FileText },
  { key: "social", label: "Social Content", icon: Share2 },
  { key: "feedback", label: "Comments & Reviews", icon: MessageSquare },
  { key: "notifications", label: "Notifications", icon: Bell },
  { key: "settings", label: "Profile & Settings", icon: Settings },
];

// ── User Sidebar ──
function UserSidebar({ activeTab, onTabChange, sessions, onNewProject, collapsed, onToggleCollapse }) {
  return (
    <aside className={`ud-sidebar-v2 ${collapsed ? "collapsed" : ""}`}>
      <div className="ud-sidebar-v2-inner">
        <div className="ud-sidebar-v2-header">
          <div className="ud-sidebar-v2-label-row">
            <button className="ud-sidebar-v2-toggle" onClick={onToggleCollapse} title={collapsed ? "Expand menu" : "Collapse menu"}>
              <Menu size={18} />
            </button>
            {!collapsed && <span className="ud-sidebar-v2-label">Menu</span>}
          </div>
          {!collapsed && <h3 className="ud-sidebar-v2-title">Brand Creator</h3>}
        </div>

        <nav className="ud-sidebar-v2-nav">
          {USER_SIDEBAR_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={`ud-sidebar-v2-item ${activeTab === item.key ? "active" : ""}`}
                onClick={() => onTabChange(item.key)}
                title={collapsed ? item.label : ""}
              >
                <Icon size={18} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="ud-sidebar-v2-new">
          <button className="ud-sidebar-v2-new-btn" onClick={onNewProject}>
            <Plus size={16} /> {!collapsed && "New Session"}
          </button>
        </div>
      </div>
    </aside>
  );
}

// ── Stats Card ──
function StatsCard({ title, value, icon: Icon, color }) {
  return (
    <div className="ud-stat-card-v2">
      <div className="ud-stat-content-v2">
        <p className="ud-stat-title-v2">{title}</p>
        <h2 className="ud-stat-value-v2">{value}</h2>
      </div>
      <div className="ud-stat-icon-v2" style={{ background: color }}>
        <Icon size={24} color="#fff" />
      </div>
    </div>
  );
}

// ── Branding Journey Progress ──
function JourneyProgress({ items }) {
  if (!items || items.length === 0) return null;
  const stageOrder = ["Basic", "Foundation", "Identity", "More", "Complete"];

  return (
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <TrendingUp size={20} /> Branding Journey Progress
      </h3>
      <div className="ud-journey-list">
        {items.map((item, i) => (
          <div key={i} className="ud-journey-item">
            <div className="ud-journey-header">
              <span className="ud-journey-name">{item.title}</span>
              <span className="ud-journey-pct">{item.progress}%</span>
            </div>
            <div className="ud-journey-bar-wrap">
              <div className="ud-journey-bar-fill" style={{ width: `${Math.min(item.progress, 100)}%` }} />
            </div>
            <div className="ud-journey-stages">
              {stageOrder.map((stage, idx) => (
                <span key={idx} className={`ud-stage-dot ${
                  item.current_stage === stage ? "current" : stageOrder.indexOf(item.current_stage) > idx ? "done" : ""
                }`}>
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

// ── AI Suggestions ──
function AISuggestions({ suggestions }) {
  if (!suggestions || suggestions.length === 0) return null;
  return (
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <Sparkles size={20} /> AI Suggestions
      </h3>
      <div className="ud-suggestions-list">
        {suggestions.map((s, i) => (
          <div key={i} className={`ud-suggestion-item ${s.type}`}>
            {s.type === "warning" ? <AlertTriangle size={16} /> : <Sparkles size={16} />}
            <p>{s.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Continue Session CTA ──
function ContinueSessionCTA({ latestSessionId, sessions, onContinue }) {
  if (!latestSessionId) return null;
  const session = sessions.find((s) => s.id === latestSessionId);
  if (!session || session.status === "completed") return null;

  return (
    <div className="ud-cta-card" onClick={() => onContinue(session)}>
      <div className="ud-cta-content">
        <h3>Continue Brand Discovery</h3>
        <p>{session.title} - {session.status === "in_progress" ? "In Progress" : "Draft"}</p>
      </div>
      <ArrowRight size={24} />
    </div>
  );
}

// ── Agency Feedback ──
function AgencyFeedback({ feedback }) {
  if (!feedback || feedback.length === 0) return null;
  return (
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <MessageSquare size={20} /> Agency Feedback
      </h3>
      <div className="ud-feedback-list">
        {feedback.map((f, i) => (
          <div key={i} className={`ud-feedback-item ${f.is_resolved ? "resolved" : ""}`}>
            <div className="ud-feedback-quote">"{f.comment}"</div>
            <div className="ud-feedback-meta">
              <span>{f.session_title}</span>
              <span className="ud-feedback-by">— {f.by}</span>
              {f.is_resolved && <CheckCircle size={14} className="ud-feedback-resolved" />}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Manifesto Preview ──
function ManifestoPreview({ preview, onView, onDownload }) {
  if (!preview) return null;
  return (
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <FileText size={20} /> Manifesto Preview
      </h3>
      <div className="ud-manifesto-preview">
        <div className="ud-manifesto-status">
          <Star size={18} />
          <span>Status: <strong>{preview.status}</strong></span>
        </div>
        {preview.has_content && (
          <div className="ud-manifesto-actions">
            <button className="ud-btn-outline" onClick={onView}>
              <Edit3 size={14} /> View / Edit
            </button>
            <button className="ud-btn-outline" onClick={onDownload}>
              <Download size={14} /> Download PDF
            </button>
          </div>
        )}
        <p className="ud-manifesto-date">Generated: {new Date(preview.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  );
}

// ── Recent Activities ──
function RecentActivities({ activities }) {
  if (!activities || activities.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case "answer_updated": return <Activity size={16} className="ud-act-icon update" />;
      case "manifesto_generated": return <FileText size={16} className="ud-act-icon manifesto" />;
      default: return <Activity size={16} className="ud-act-icon" />;
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
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <Activity size={20} /> Recent Activities
      </h3>
      <div className="ud-activity-list">
        {activities.map((act, i) => (
          <div key={i} className="ud-activity-item">
            {getIcon(act.type)}
            <div>
              <p className="ud-activity-msg">{act.message}</p>
              <p className="ud-activity-time">{formatTime(act.timestamp)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Sessions Table ──
function SessionsTable({ sessions, onView, onContinue, onToggleLock, onLoadComments }) {
  const getStatusDisplay = (session) => {
    switch ((session.status || "").toLowerCase()) {
      case "draft": return "Draft";
      case "in_progress": return "In Progress";
      case "completed": return "Completed";
      default: return session.status || "Draft";
    }
  };

  return (
    <div className="ud-section-card">
      <h3 className="ud-section-heading">
        <FolderOpen size={20} /> All Sessions
      </h3>
      <div className="ud-table-v2-wrap">
        <table className="ud-table-v2">
          <thead>
            <tr>
              <th>Sr.No.</th>
              <th>Project Name</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Brand Stage</th>
              <th>Locked</th>
              <th>Action</th>
              <th>Comments</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session, idx) => {
              const isCompleted = session.is_complete || session.status === "completed";
              return (
                <tr key={session.id || idx}>
                  <td className="ud-td-idx">{idx + 1}</td>
                  <td className="ud-td-name-v2">{session.title}</td>
                  <td>
                    <div className="ud-status-v2">
                      <span className={`ud-dot-v2 ${isCompleted ? "completed" : "progress"}`} />
                      <span>{getStatusDisplay(session)}</span>
                    </div>
                  </td>
                  <td>
                    <div className="ud-mini-progress">
                      <div className="ud-mini-progress-fill" style={{ width: `${session.progress ?? 0}%` }} />
                      <span>{Math.round(session.progress ?? 0)}%</span>
                    </div>
                  </td>
                  <td>{session.stage || "Foundation"}</td>
                  <td>
                    <label className="ud-lock-switch">
                      <input type="checkbox" checked={!session.is_locked} onChange={() => onToggleLock(session)} />
                      <span className="ud-switch-slider" />
                    </label>
                  </td>
                  <td>
                    {isCompleted ? (
                      <button className="ud-btn-sm-v2 view" onClick={() => onView(session)}>View</button>
                    ) : (
                      <button className="ud-btn-sm-v2 continue" onClick={() => onContinue(session)}>Continue</button>
                    )}
                  </td>
                  <td>
                    <button className="ud-btn-sm-v2 view" onClick={() => onLoadComments(session.id)} disabled={!isCompleted}>
                      Comments
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Foundation Modal (kept from original) ──
function FoundationModal({ show, onClose, onSubmit, loading, error, agencies, agenciesLoading, agenciesError, hasExistingSessions }) {
  const [modalTitle, setModalTitle] = useState("");
  const [selectedAgency, setSelectedAgency] = useState(0);
  const [modalTouched, setModalTouched] = useState(false);

  useEffect(() => { if (agencies.length > 0) setSelectedAgency(agencies[0].id ?? agencies[0].pk ?? 0); }, [agencies]);
  useEffect(() => { if (!show) { setModalTitle(""); setModalTouched(false); } }, [show]);

  const isValid = modalTitle.trim().length > 0;
  const handleSubmit = (e) => { e.preventDefault(); setModalTouched(true); if (!isValid) return; onSubmit({ title: modalTitle.trim(), agency: Number(selectedAgency) || null }); };
  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content foundation-modal" onClick={(e) => e.stopPropagation()}>
        <button className="foundation-modal-close" onClick={onClose} type="button" disabled={loading}>×</button>
        <div className="modal-header"><h2>Create New Session</h2><p>Start a new brand journey.</p></div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="sessionTitle">Session Title *</label>
            <input id="sessionTitle" type="text" placeholder="e.g., My Brand Strategy 2025" value={modalTitle} onChange={(e) => setModalTitle(e.target.value)} className={modalTouched && !isValid ? "input-error" : ""} disabled={loading} autoFocus />
            {modalTouched && !isValid && <span className="error-text">Session title is required</span>}
          </div>
          <div className="form-group">
            <label htmlFor="agency">Select Agency (Optional)</label>
            {agenciesLoading ? <p className="loading-text">Loading agencies...</p> : agenciesError ? <p className="error-text">{agenciesError}</p> : (
              <select id="agency" value={selectedAgency} onChange={(e) => setSelectedAgency(e.target.value)} disabled={loading || agencies.length === 0}>
                <option value={0}>-- No Agency --</option>
                {agencies.map((ag) => <option key={ag.id ?? ag.pk} value={ag.id ?? ag.pk}>{ag.name || ag.title || `Agency ${ag.id}`}</option>)}
              </select>
            )}
          </div>
          {error && <div className="error-banner"><p>{error}</p></div>}
          <div className="modal-actions">
            {hasExistingSessions && <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>Cancel</button>}
            <button type="submit" className="btn-primary" disabled={loading || !isValid}>{loading ? "Creating..." : "Create Session"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main User Dashboard ──
export default function UserDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboardData, setDashboardData] = useState(null);

  // Modal state
  const [showFoundationModal, setShowFoundationModal] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");
  const [agencies, setAgencies] = useState([]);
  const [agenciesLoading, setAgenciesLoading] = useState(false);
  const [agenciesError, setAgenciesError] = useState("");

  // Comments modal
  const [commentsModalOpen, setCommentsModalOpen] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await authService.getUserDashboard();
      setDashboardData(data);
      if (!data.sessions || data.sessions.length === 0) {
        setShowFoundationModal(true);
        loadAgencies();
      }
    } catch (err) {
      setError(err?.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  const loadAgencies = async () => {
    setAgenciesLoading(true);
    try {
      const data = await authService.getAgencies();
      setAgencies(Array.isArray(data) ? data : []);
    } catch (err) {
      setAgenciesError(err.message || "Failed to load agencies");
    } finally {
      setAgenciesLoading(false);
    }
  };

  const loadComments = async (sessionId) => {
    setCommentsLoading(true);
    try {
      const fetched = await authService.getComments(sessionId);
      setComments(fetched);
      setCommentsModalOpen(true);
    } catch { toast.error("Failed to load comments"); }
    finally { setCommentsLoading(false); }
  };

  const handleCreateSession = async (payload) => {
    setModalLoading(true);
    setModalError("");
    try {
      const data = await authService.createSession(payload);
      const sessionObj = data?.session || data;
      localStorage.setItem("session", JSON.stringify(sessionObj));
      if (sessionObj.id) localStorage.setItem("sessionId", String(sessionObj.id));
      toast.success("Session created successfully!");
      setShowFoundationModal(false);
      navigate("/phase-questions/1");
    } catch (err) {
      setModalError(err.message || "Failed to create session.");
      toast.error(err.message);
    } finally {
      setModalLoading(false);
    }
  };

  const handleNewSession = () => { loadAgencies(); setShowFoundationModal(true); };

  const handleViewSession = (session) => {
    localStorage.setItem("session", JSON.stringify(session));
    if (session.id) localStorage.setItem("sessionId", String(session.id));
    navigate("/manifesto");
  };

  const handleContinueSession = (session) => {
    localStorage.setItem("session", JSON.stringify(session));
    if (session.id) localStorage.setItem("sessionId", String(session.id));
    navigate("/phase-questions/1");
  };

  const handleToggleLock = async (session) => {
    try {
      if (session.is_locked) { await authService.unlockSession(session.id); toast.success("Session unlocked!"); }
      else { await authService.lockSession(session.id); toast.success("Session locked!"); }
      fetchDashboard();
    } catch (err) { toast.error(err.message || "Failed to update lock"); }
  };

  const handleDownloadManifesto = async () => {
    const sessionId = dashboardData?.latest_session_id;
    if (!sessionId) return;
    try {
      const blob = await authService.downloadManifesto(sessionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "manifesto.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) { toast.error("Download failed"); }
  };

  const stats = dashboardData?.stats || {};
  const sessions = dashboardData?.sessions || [];

  const statCards = [
    { title: "Current Stage", value: stats.current_stage ?? "—", icon: Layers, color: "rgba(57, 89, 229, 0.8)" },
    { title: "Completion", value: `${stats.completion_pct ?? 0}%`, icon: TrendingUp, color: "rgba(142, 229, 255, 0.8)" },
    { title: "AI Quality Score", value: `${stats.ai_quality_score ?? 0}%`, icon: Sparkles, color: "rgba(168, 130, 255, 0.8)" },
    { title: "Pending Feedback", value: stats.pending_feedback ?? 0, icon: MessageSquare, color: "rgba(255, 195, 134, 0.8)" },
    { title: "Uploaded Documents", value: stats.uploaded_documents ?? 0, icon: FileUp, color: "rgba(134, 227, 100, 0.8)" },
    { title: "Manifesto Status", value: stats.manifesto_status ?? "—", icon: FileText, color: "rgba(255, 107, 107, 0.8)" },
  ];

  // ── Tab content rendering ──
  const renderContent = () => {
    if (loading) return <div className="ud-loading-v2">Loading your dashboard...</div>;
    if (error) return <div className="ud-error-v2">Error: {error}</div>;

    switch (activeTab) {
      case "dashboard":
        return (
          <>
            <div className="ud-stats-grid-v2">
              {statCards.map((s) => <StatsCard key={s.title} {...s} />)}
            </div>
            <ContinueSessionCTA latestSessionId={dashboardData?.latest_session_id} sessions={sessions} onContinue={handleContinueSession} />
            <div
              className="ud-redirect-card"
              style={{ marginTop: "1rem" }}
              onClick={() => navigate("/brand-os")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && navigate("/brand-os")}
            >
              <h3>Brand Operating System</h3>
              <p>Run DNA, messaging, tone, positioning — with explainability and feedback learning.</p>
              <span className="ud-redirect-link">Open Brand OS <ArrowRight size={16} /></span>
            </div>
            <div
              className="ud-redirect-card"
              style={{ marginTop: "0.75rem" }}
              onClick={() => navigate("/brand-onboarding")}
              role="button"
              tabIndex={0}
            >
              <h3>Getting started</h3>
              <p>4-step onboarding: upload → generate → refine → export PDF/PPT.</p>
              <span className="ud-redirect-link">Start onboarding <ArrowRight size={16} /></span>
            </div>
            <div className="ud-two-col">
              <JourneyProgress items={dashboardData?.journey_progress} />
              <AISuggestions suggestions={dashboardData?.ai_suggestions} />
            </div>
            <AgencyFeedback feedback={dashboardData?.agency_feedback} />
            <div className="ud-two-col">
              <ManifestoPreview
                preview={dashboardData?.manifesto_preview}
                onView={() => { if (dashboardData?.latest_session_id) handleViewSession({ id: dashboardData.latest_session_id }); }}
                onDownload={handleDownloadManifesto}
              />
              <RecentActivities activities={dashboardData?.recent_activities} />
            </div>
          </>
        );
      case "sessions":
        return (
          <>
            <h2 className="ud-tab-title">My Projects / Sessions</h2>
            <SessionsTable sessions={sessions} onView={handleViewSession} onContinue={handleContinueSession} onToggleLock={handleToggleLock} onLoadComments={loadComments} />
          </>
        );
      case "foundation":
        return (
          <div className="ud-redirect-card" onClick={() => {
            const s = sessions[0];
            if (s) { localStorage.setItem("session", JSON.stringify(s)); localStorage.setItem("sessionId", String(s.id)); }
            navigate("/phase-questions/1");
          }}>
            <Layers size={32} />
            <h3>Foundation Questions</h3>
            <p>Answer the foundation questions to build your brand identity.</p>
            <ArrowRight size={20} />
          </div>
        );
      case "discovery":
        return (
          <div className="ud-redirect-card" onClick={() => navigate("/ChatKickoffPage")}>
            <MessageCircle size={32} />
            <h3>Brand Discovery Chat</h3>
            <p>Start an AI-powered conversation to discover your brand voice.</p>
            <ArrowRight size={20} />
          </div>
        );
      case "deepdive":
        return (
          <div className="ud-redirect-card" onClick={() => navigate("/DeepDivePage")}>
            <Compass size={32} />
            <h3>Deep Dive</h3>
            <p>Advanced branding questions to refine your positioning.</p>
            <ArrowRight size={20} />
          </div>
        );
      case "documents":
        return (
          <div className="ud-placeholder-v2"><FileUp size={48} /><p>Document management coming soon.</p></div>
        );
      case "ai-suggestions":
        return (
          <>
            <h2 className="ud-tab-title">AI Suggestions</h2>
            <AISuggestions suggestions={dashboardData?.ai_suggestions} />
          </>
        );
      case "manifesto":
        return (
          <>
            <h2 className="ud-tab-title">Manifesto</h2>
            <ManifestoPreview
              preview={dashboardData?.manifesto_preview}
              onView={() => { if (dashboardData?.latest_session_id) handleViewSession({ id: dashboardData.latest_session_id }); }}
              onDownload={handleDownloadManifesto}
            />
          </>
        );
      case "social":
        return (
          <div className="ud-placeholder-v2"><Share2 size={48} /><p>AI-generated social content coming soon.</p></div>
        );
      case "feedback":
        return (
          <>
            <h2 className="ud-tab-title">Comments & Reviews</h2>
            <AgencyFeedback feedback={dashboardData?.agency_feedback} />
          </>
        );
      case "notifications":
        return (
          <>
            <h2 className="ud-tab-title">Notifications</h2>
            <RecentActivities activities={dashboardData?.recent_activities} />
          </>
        );
      case "settings":
        return (
          <div className="ud-placeholder-v2"><Settings size={48} /><p>Profile & Settings coming soon.</p></div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="ud-root-v2">
      <div className="ud-bg-v2"><div className="ud-bg-orb-v2" /></div>
      <ChatNavbar showSaveButton={false} showDownloadButton={false} showLogoutButton={true} />
      <div className="ud-page-v2">
        <UserSidebar activeTab={activeTab} onTabChange={setActiveTab} sessions={sessions} onNewProject={handleNewSession} collapsed={sidebarCollapsed} onToggleCollapse={() => setSidebarCollapsed(c => !c)} />
        <main className="ud-main-v2">
          <div className="ud-main-inner-v2">
            <h1 className="ud-heading-v2">User Dashboard</h1>
            <div className="user-bg-animate">
              <div className="bg-glow gl-1"></div>
              <div className="bg-glow gl-2"></div>
              <div className="bg-glow gl-3"></div>
              {renderContent()}
            </div>
          </div>
        </main>
      </div>

      <FoundationModal
        show={showFoundationModal}
        onClose={() => { if (sessions.length === 0) { toast.info("Please create a session"); return; } setShowFoundationModal(false); }}
        onSubmit={handleCreateSession}
        loading={modalLoading}
        error={modalError}
        agencies={agencies}
        agenciesLoading={agenciesLoading}
        agenciesError={agenciesError}
        hasExistingSessions={sessions.length > 0}
      />

      <CommentsModal isOpen={commentsModalOpen} onClose={() => setCommentsModalOpen(false)} comments={comments} loading={commentsLoading} />
    </div>
  );
}
