import React, { useEffect, useMemo, useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ChatNavbar from "./ChatNavbar";
import authService from "../services/authService";
import "../components/ManifestoPage.css";

function normalizeType(t) {
  const v = String(t || "").toLowerCase();
  if (["heading", "section", "title", "header", "h1", "h2"].includes(v)) return "heading";
  if (["subheading", "subsection", "subtitle", "h3", "h4"].includes(v)) return "subsection";
  if (["list_item", "bullet", "bullet_point"].includes(v)) return "bullet";
  if (["numbered_item", "numbered"].includes(v)) return "numbered";
  return "body";
}

function toText(item) {
  const raw = item?.text ?? item?.content ?? item?.label ?? item?.body ?? "";
  if (typeof raw === "string") return raw.trim();
  if (Array.isArray(raw)) return raw.map((x) => (typeof x === "string" ? x : x?.text ?? x?.content ?? "")).join("\n").trim();
  if (raw && typeof raw === "object") return String(raw.text ?? raw.content ?? "").trim();
  return "";
}

function toSummaryString(raw) {
  if (raw == null) return "";
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) return raw.map((x) => (typeof x === "string" ? x : x?.text ?? x?.content ?? "")).join("\n");
  if (typeof raw === "object") return String(raw.text ?? raw.content ?? "");
  return "";
}

function parseStringSummary(raw) {
  const str = toSummaryString(raw);
  if (!str) return { title: "Brand Manifesto", elements: [] };
  const lines = str.split("\n").map((x) => x.trim()).filter(Boolean);
  let title = "Brand Manifesto";
  const elements = [];

  lines.forEach((line, idx) => {
    if (idx === 0 && line.startsWith("**") && line.endsWith("**")) {
      title = line.replace(/\*\*/g, "");
      return;
    }
    if (line.startsWith("###")) {
      elements.push({ type: "subsection", text: line.replace(/^#+\s*/, ""), key: idx });
      return;
    }
    if ((line.startsWith("**") && line.endsWith("**")) || /^#{1,2}\s+/.test(line)) {
      elements.push({ type: "heading", text: line.replace(/\*\*/g, "").replace(/^#{1,2}\s*/, ""), key: idx });
      return;
    }
    if (/^\d+\./.test(line)) {
      elements.push({ type: "numbered", text: line.replace(/^\d+\.\s*/, ""), key: idx });
      return;
    }
    if (line.startsWith("-")) {
      elements.push({ type: "bullet", text: line.replace(/^-\s*/, ""), key: idx });
      return;
    }
    elements.push({ type: "body", text: line, key: idx });
  });

  return { title, elements };
}

function parseStructuredSummary(resp) {
  const sections = resp?.sections ?? resp?.blocks ?? resp?.content ?? [];
  if (!Array.isArray(sections) || sections.length === 0) return null;
  
  // Extract title, heading, subheading, and quote from API response
  const title = resp?.title || resp?.brand_name || resp?.brandName || "Brand Manifesto";
  const heading = resp?.heading || resp?.headline || null;
  const subheading = resp?.subheading || resp?.sub_headline || resp?.subtitle || null;
  const quote = resp?.quote || resp?.quote_text || resp?.intro_quote || null;
  
  const elements = sections
    .map((item, idx) => ({ type: normalizeType(item?.type), text: toText(item), key: idx }))
    .filter((x) => x.text);
  
  return { title, heading, subheading, quote, elements };
}

function extractManifestoContent(resp) {
  if (!resp || typeof resp !== "object") {
    const parsed = parseStringSummary(resp);
    return { ...parsed, heading: null, subheading: null, quote: null };
  }
  const direct = parseStructuredSummary(resp);
  if (direct) return direct;
  const dataStructured = parseStructuredSummary(resp?.data);
  if (dataStructured) return dataStructured;
  const summaryStructured = parseStructuredSummary(resp?.summary);
  if (summaryStructured) return summaryStructured;
  const parsed = parseStringSummary(resp?.summary ?? resp);
  return { ...parsed, heading: null, subheading: null, quote: null };
}

// Magazine-style components
function ManifestoTitle({ children }) {
  if (!children) return null;
  return <h1 className="mfp-magazine-title">{children}</h1>;
}

function ManifestoHeading({ children }) {
  if (!children) return null;
  return <h2 className="mfp-magazine-heading">{children}</h2>;
}

function ManifestoSubheading({ children }) {
  if (!children) return null;
  return <h3 className="mfp-magazine-subheading">{children}</h3>;
}

function ManifestoQuote({ children }) {
  if (!children) return null;
  return (
    <blockquote className="mfp-magazine-quote">
      <span className="mfp-quote-mark">"</span>
      {children}
      <span className="mfp-quote-mark">"</span>
    </blockquote>
  );
}

function Row({ item }) {
  if (item.type === "heading") return <h3 className="mfp-h3">{item.text}</h3>;
  if (item.type === "subsection") return <h4 className="mfp-h4">{item.text}</h4>;
  if (item.type === "bullet") return <li className="mfp-li">◆ {item.text}</li>;
  if (item.type === "numbered") return <li className="mfp-li">▸ {item.text}</li>;
  return <p className="mfp-p">{item.text}</p>;
}

export default function ManifestoPage() {
  const navigateRef = useRef(null);
  const navigateOriginal = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("Brand Manifesto");
  const [heading, setHeading] = useState(null);
  const [subheading, setSubheading] = useState(null);
  const [quote, setQuote] = useState(null);
  const [elements, setElements] = useState([]);
  const [stage, setStage] = useState("cover");
  const [rawApiResponse, setRawApiResponse] = useState(null);
  const [allowNavigation, setAllowNavigation] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(60); // Zoom level in percentage - forced to 60%

  // Use original navigate - the history override will handle blocking auto-redirects
  const navigate = navigateOriginal;

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoomLevel((prev) => Math.min(prev + 10, 200)); // Max 200%
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel((prev) => Math.max(prev - 10, 50)); // Min 50%
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoomLevel(60); // Reset to 60%
  }, []);

  // Handler for copying API response to clipboard
  const handleCopyApiData = useCallback(async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      if (e.nativeEvent) {
        e.nativeEvent.stopImmediatePropagation();
      }
    }
    
    if (!rawApiResponse) return;
    
    try {
      const jsonString = JSON.stringify(rawApiResponse, null, 2);
      await navigator.clipboard.writeText(jsonString);
      // Show success feedback (you can use toast here if available)
      alert('API data copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy:', err);
      alert('Failed to copy API data. Please try again.');
    }
  }, [rawApiResponse]);

  // Block only automatic navigation/redirects, allow user clicks
  useEffect(() => {
    let isUserClick = false;
    let clickTimeout = null;
    
    // Track user clicks
    const handleMouseDown = () => {
      isUserClick = true;
      if (clickTimeout) clearTimeout(clickTimeout);
      clickTimeout = setTimeout(() => {
        isUserClick = false;
      }, 100); // Allow navigation within 100ms of click
    };
    
    // Track keyboard interactions (user-initiated)
    const handleKeyDown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        isUserClick = true;
        if (clickTimeout) clearTimeout(clickTimeout);
        clickTimeout = setTimeout(() => {
          isUserClick = false;
        }, 100);
      }
    };
    
    // Store original pushState and replaceState
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    // Override pushState - only block if it's NOT from user click
    history.pushState = function(...args) {
      // Allow if user clicked, or if allowNavigation is explicitly set
      if (isUserClick || allowNavigation) {
        return originalPushState.apply(history, args);
      }
      // Block automatic redirects
      console.log('Auto-redirect blocked:', args);
      return;
    };
    
    // Override replaceState - only block if it's NOT from user click
    history.replaceState = function(...args) {
      // Allow if user clicked, or if allowNavigation is explicitly set
      if (isUserClick || allowNavigation) {
        return originalReplaceState.apply(history, args);
      }
      // Block automatic redirects
      console.log('Auto-redirect blocked:', args);
      return;
    };
    
    // Add event listeners to track user interactions
    window.addEventListener('mousedown', handleMouseDown, true);
    window.addEventListener('keydown', handleKeyDown, true);
    
    return () => {
      // Restore original functions on unmount
      history.pushState = originalPushState;
      history.replaceState = originalReplaceState;
      window.removeEventListener('mousedown', handleMouseDown, true);
      window.removeEventListener('keydown', handleKeyDown, true);
      if (clickTimeout) clearTimeout(clickTimeout);
    };
  }, [allowNavigation]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);
        setError("");
        let sessionId = localStorage.getItem("sessionId");
        if (!sessionId) {
          const raw = localStorage.getItem("session");
          const session = raw ? JSON.parse(raw) : null;
          sessionId = session?.id ?? session?.pk ?? null;
        }
        // Don't throw error - just show error message, don't redirect
        if (!sessionId) {
          if (!cancelled) {
            setError("No session found. Please complete the foundation questions first.");
            setLoading(false);
          }
          return;
        }

        let payload = null;
        try {
          payload = await authService.getFoundationSummary(sessionId);
        } catch (_) {}

        if (!payload || Object.keys(payload || {}).length === 0) {
          payload = await authService.generateSessionSummary(sessionId);
        }

        // Store raw API response for debugging
        if (!cancelled) {
          setRawApiResponse(payload);
        }

        const parsed = extractManifestoContent(payload);
        if (!cancelled) {
          setTitle(parsed.title || "Brand Manifesto");
          setHeading(parsed.heading || null);
          setSubheading(parsed.subheading || null);
          setQuote(parsed.quote || null);
          setElements(parsed.elements || []);
          setStage("cover");
          setTimeout(() => {
            if (!cancelled) setStage("content");
          }, 850);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e?.message || "Failed to load manifesto");
          setLoading(false);
          // Don't redirect on error - stay on page
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  // Single continuous flow instead of two columns
  // const [left, right] = useMemo(() => {
  //   const mid = Math.ceil(elements.length / 2);
  //   return [elements.slice(0, mid), elements.slice(mid)];
  // }, [elements]);

  if (loading) {
    return (
      <div className="mfp-state">
        <div className="mfp-spinner" />
        <p>Preparing manifesto...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mfp-state">
        <p className="mfp-error">{error}</p>
        <button 
          className="mfp-btn" 
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            navigate("/ChatKickoffPage");
          }}
          type="button"
        >
          Back to Chat
        </button>
      </div>
    );
  }

  return (
    <>
      <ChatNavbar showSaveButton={false} showDownloadButton={false} />
      <div className="mfp-wrap" style={{ '--zoom-level': zoomLevel }}>
        {stage === "cover" ? (
          <div className="mfp-cover">
            <h1>Brand Manifesto</h1>
            <h2>{title}</h2>
          </div>
        ) : (
          <>
            <div className="mfp-book">
              <section className="mfp-page mfp-page-single">
                {/* Magazine-style layout */}
                <ManifestoTitle>{title}</ManifestoTitle>
                {heading && <ManifestoHeading>{heading}</ManifestoHeading>}
                {subheading && <ManifestoSubheading>{subheading}</ManifestoSubheading>}
                {quote && <ManifestoQuote>{quote}</ManifestoQuote>}
                
                {/* Content elements */}
                {elements.map((item) => (
                  <Row key={item.key} item={item} />
                ))}
              </section>
            </div>

            {/* Zoom Controls - Right Side Vertical */}
            <div className="mfp-zoom-controls-vertical">
              <button 
                className="mfp-zoom-btn-vertical" 
                onClick={handleZoomIn}
                type="button"
                title="Zoom In"
                disabled={zoomLevel >= 200}
              >
                +
              </button>
              <span className="mfp-zoom-level-vertical">{zoomLevel}%</span>
              <button 
                className="mfp-zoom-btn-vertical" 
                onClick={handleZoomReset}
                type="button"
                title="Reset Zoom"
              >
                ⟲
              </button>
              <button 
                className="mfp-zoom-btn-vertical" 
                onClick={handleZoomOut}
                type="button"
                title="Zoom Out"
                disabled={zoomLevel <= 50}
              >
                −
              </button>
            </div>
          </>
        )}

        <div className="mfp-actions">
          <button 
            className="mfp-btn mfp-btn-light" 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              navigate("/ChatKickoffPage");
            }}
            type="button"
          >
            Back
          </button>
          {rawApiResponse != null && (
            <button 
              className="mfp-btn mfp-btn-light" 
              onClick={handleCopyApiData}
              onMouseDown={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              type="button"
              style={{ pointerEvents: 'auto' }}
            >
              Copy API Data
            </button>
          )}
          <button 
            className="mfp-btn" 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              window.print();
            }}
            type="button"
          >
            Print PDF
          </button>
        </div>

      </div>
    </>
  );
}
