import { useEffect, useMemo, useState } from "react";
import authService from "../services/authService";
import { selectStrategicQuote } from "../utils/strategicQuotes";
import "./StrategicQuoteMoment.css";

function getStorageFlag(storageKey) {
  if (!storageKey) return false;
  try {
    return sessionStorage.getItem(storageKey) === "1";
  } catch {
    return false;
  }
}

function setStorageFlag(storageKey) {
  if (!storageKey) return;
  try {
    sessionStorage.setItem(storageKey, "1");
  } catch {
    /* ignore */
  }
}

export default function StrategicQuoteMoment({
  context,
  phaseId,
  sourceText = "",
  variant = "inline",
  eyebrow,
  storageKey,
  ctaLabel = "Continue",
  className = "",
}) {
  const sessionId = useMemo(() => {
    try {
      return localStorage.getItem("sessionId") || "";
    } catch {
      return "";
    }
  }, []);
  const resolvedStorageKey = storageKey ? `${storageKey}:${sessionId || "anon"}` : "";
  const fallbackQuote = useMemo(
    () => selectStrategicQuote({ context, phaseId, sourceText }),
    [context, phaseId, sourceText],
  );
  const [quote, setQuote] = useState(fallbackQuote);
  const [open, setOpen] = useState(() => variant === "overlay" && !getStorageFlag(resolvedStorageKey));

  useEffect(() => {
    setQuote(fallbackQuote);
  }, [fallbackQuote]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    async function loadQuote() {
      try {
        const data = await authService.getStrategicQuote(sessionId, { context, phaseId, sourceText });
        if (cancelled || !data?.text) return;
        setQuote({
          id: `api-${data.context || context}-${data.phase_id || phaseId}`,
          text: data.text,
          author: data.author || "The Brand Godfather",
          source: data.source || "llm",
          evidence: data.evidence || "Generated from this session's strategic context.",
          role: data.role,
        });
      } catch {
        /* keep local fallback */
      }
    }

    loadQuote();
    return () => {
      cancelled = true;
    };
  }, [context, fallbackQuote, phaseId, sessionId, sourceText]);

  useEffect(() => {
    if (variant === "overlay") {
      setOpen(!getStorageFlag(resolvedStorageKey));
    }
  }, [resolvedStorageKey, variant]);

  const close = () => {
    setStorageFlag(resolvedStorageKey);
    setOpen(false);
  };

  const quoteMarkup = (
    <figure className={`sqm-card sqm-card--${variant} ${quote.source === "user" ? "sqm-card--user" : ""} ${className}`}>
      <figcaption className="sqm-eyebrow">{eyebrow || (quote.source === "user" ? "From your own words" : "Strategic reflection")}</figcaption>
      <blockquote className="sqm-text">{quote.text}</blockquote>
      <p className="sqm-author">- {quote.author}</p>
      {variant === "overlay" && (
        <button type="button" className="sqm-continue" onClick={close}>
          {ctaLabel}
        </button>
      )}
    </figure>
  );

  if (variant !== "overlay") return quoteMarkup;
  if (!open) return null;

  return (
    <div className="sqm-overlay" role="dialog" aria-modal="true" aria-label="Strategic reflection">
      {quoteMarkup}
    </div>
  );
}