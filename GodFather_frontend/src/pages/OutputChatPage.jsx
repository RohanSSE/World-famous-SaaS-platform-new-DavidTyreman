import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import ChatNavbar from "./ChatNavbar";
import authService from "../services/authService";
import "./OutputChatPage.css";

const introMessage = {
  id: "intro",
  role: "assistant",
  content:
    "I'm here to help you turn your Brand Book into strategic promotion. Choose a direction, or ask me anything about campaigns, messaging, trust, visibility, or growth opportunities.",
};

const PROMOTION_STARTER_STORAGE_KEY = "brandPromotionStarter";
const PROMOTION_STARTER_CONSUMED_KEY = "brandPromotionStarterConsumed";

function getStoredPromotionStarter() {
  try {
    return JSON.parse(sessionStorage.getItem(PROMOTION_STARTER_STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

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
  const location = useLocation();
  const autoStartRef = useRef(false);
  const promotionStarter = useMemo(
    () => location.state?.promotionStarter || getStoredPromotionStarter(),
    [location.state]
  );
  const [messages, setMessages] = useState([introMessage]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [activeStarterGoal, setActiveStarterGoal] = useState(promotionStarter?.goal || "");

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

  const sendQuestion = useCallback(
    async (rawQuestion, options = {}) => {
      const question = rawQuestion.trim();
      const displayContent = (options.displayContent || question).trim();

      if (!question || isSending) return;

      const userMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: displayContent,
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
    },
    [conversationMessages, isSending]
  );

  useEffect(() => {
    if (!promotionStarter?.prompt || autoStartRef.current) return;

    const starterId = promotionStarter.id || promotionStarter.goal || promotionStarter.prompt;

    try {
      if (sessionStorage.getItem(PROMOTION_STARTER_CONSUMED_KEY) === starterId) return;
    } catch {
      // Continue with route state when browser storage is unavailable.
    }

    autoStartRef.current = true;

    try {
      sessionStorage.setItem(PROMOTION_STARTER_CONSUMED_KEY, starterId);
      sessionStorage.removeItem(PROMOTION_STARTER_STORAGE_KEY);
    } catch {
      // The selected starter can still be sent from route state.
    }

    setActiveStarterGoal(promotionStarter.goal || "");

    sendQuestion(promotionStarter.prompt, {
      displayContent: promotionStarter.goal || "Start Brand Promotion Phase",
    });
  }, [promotionStarter, sendQuestion]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await sendQuestion(inputValue);
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

        {activeStarterGoal && (
          <div className="ocp-context-pill">Brand Promotion Focus: {activeStarterGoal}</div>
        )}

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
