import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import authService from "../services/authService";
import "./OutputChatPage.css";

const introMessage = {
  id: "intro",
  role: "assistant",
  content:
    "I'm here to help you think strategically. Ask me anything about positioning, messaging, campaigns, or how to apply your brand identity.",
};

function getStoredSessionId() {
  const directId = localStorage.getItem("sessionId");
  if (directId) return directId;

  try {
    const storedSession = JSON.parse(localStorage.getItem("session") || "null");
    return storedSession?.id || storedSession?.session_id || null;
  } catch {
    return null;
  }
}

function getDashboardPath() {
  const user = authService.getCurrentUser();
  const roleName = (user?.role_name || "").toLowerCase();

  if (user?.is_superuser || user?.is_staff || roleName === "admin") return "/admin";
  if (roleName === "agency" || user?.role === 3) return "/agency-dashboard";
  if (roleName === "client" || user?.role === 2) return "/user-dashboard";
  return authService.isAuthenticated() ? "/welcome" : "/login";
}

export default function OutputChatPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([introMessage]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const conversationMessages = useMemo(
    () =>
      messages
        .filter((message) => message.id !== "intro")
        .map((message) => ({
          role: message.role,
          content: message.content,
        })),
    [messages]
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    const question = inputValue.trim();

    if (!question || isSending) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setInputValue("");
    setError("");
    setIsSending(true);

    try {
      const response = await authService.ragQuery(question, {
        sessionId: getStoredSessionId(),
        agentId: "strategist",
        includeUserDocs: true,
        conversationMessages: [...conversationMessages, { role: "user", content: question }],
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.answer || "I couldn't generate an answer for that yet.",
          sources: response.sources || [],
        },
      ]);
    } catch (requestError) {
      setError(requestError.message || "Something went wrong. Please try again.");
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: "I couldn't reach the brand intelligence backend right now. Please try again in a moment.",
          isError: true,
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="ocp-page">
      <header className="ocp-topbar">
        <ChatNavbar
          showSaveButton={false}
          showDownloadButton={false}
          showLogoutButton
          phaseStatus={{
            title: "Output chat",
            subtitle: "Growth mode active · Strategy chat ready",
            progress: 100,
          }}
        />
      </header>

      <main className="ocp-main">
        <div className="ocp-row">
          <button type="button" className="ocp-chip" onClick={() => navigate("/output-mode")}>
            Back
          </button>
          <button type="button" className="ocp-chip" onClick={() => navigate(getDashboardPath())}>
            Go to dashboard
          </button>
        </div>

        <div className="ocp-chat-panel" aria-live="polite">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`ocp-bubble ${message.role === "user" ? "is-user" : "is-assistant"} ${message.isError ? "is-error" : ""}`}
            >
              {message.role === "assistant" && <span className="ocp-dot" />}
              <p>{message.content}</p>
              {message.sources?.length > 0 && (
                <div className="ocp-sources">
                  {message.sources.slice(0, 3).map((source, index) => (
                    <span key={`${message.id}-source-${index}`}>
                      {source.title || source.source || source.file_name || `Source ${index + 1}`}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isSending && (
            <div className="ocp-bubble is-assistant is-loading">
              <span className="ocp-dot" />
              <p>Thinking through your brand context...</p>
            </div>
          )}
        </div>

        {error && <p className="ocp-error">{error}</p>}

        <form className="ocp-input-wrap" onSubmit={handleSubmit}>
          <input
            type="text"
            className="ocp-input"
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Ask about your brand strategy"
            aria-label="Ask about your brand strategy"
            disabled={isSending}
          />
          <button type="submit" className="ocp-send" aria-label="Send" disabled={isSending || !inputValue.trim()}>
            ➤
          </button>
        </form>
      </main>

      <div className="ocp-orb" aria-hidden="true">
        <OrbPresence>
          <BrandOrb size="welcome" />
        </OrbPresence>
      </div>
    </div>
  );
}
