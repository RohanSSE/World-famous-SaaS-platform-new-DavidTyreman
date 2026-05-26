import { useEffect, useState } from "react";
import authService from "../../services/authService";
import "./FeedbackLearningPanel.css";

export default function FeedbackLearningPanel({ sessionId, lastOutput = "", onSaved }) {
  const [edited, setEdited] = useState(lastOutput);
  const [preferredTone, setPreferredTone] = useState("");
  const [rejectPhrase, setRejectPhrase] = useState("");
  const [profile, setProfile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setEdited(lastOutput || "");
  }, [lastOutput]);

  useEffect(() => {
    if (!sessionId) return;
    authService
      .getFeedbackLearningProfile(sessionId)
      .then((d) => setProfile(d.feedback_profile || d))
      .catch(() => setProfile(null));
  }, [sessionId]);

  const saveCorrection = async () => {
    if (!sessionId || !edited.trim()) return;
    setSaving(true);
    setMessage("");
    try {
      await authService.submitFeedbackLearning(sessionId, {
        original_ai_text: lastOutput,
        edited_text: edited,
        context: preferredTone
          ? `preferred_tone: ${preferredTone}${rejectPhrase ? `; reject: ${rejectPhrase}` : ""}`
          : rejectPhrase
            ? `reject_phrase: ${rejectPhrase}`
            : "",
      });
      setMessage("Brand preference saved — cognition will adapt.");
      onSaved?.();
      const p = await authService.getFeedbackLearningProfile(sessionId);
      setProfile(p);
    } catch (e) {
      setMessage(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="feedback-learning-panel" aria-label="Human feedback learning">
      <h3>Teach the brand brain</h3>
      <p className="feedback-hint">
        Edit AI output, set tone, or reject phrases — persisted for this session.
      </p>

      <label>
        Edit AI output
        <textarea
          value={edited}
          onChange={(e) => setEdited(e.target.value)}
          rows={6}
          placeholder="Correct strategic wording…"
        />
      </label>

      <label>
        Preferred tone
        <input
          type="text"
          value={preferredTone}
          onChange={(e) => setPreferredTone(e.target.value)}
          placeholder="e.g. authoritative, warm, premium"
        />
      </label>

      <label>
        Reject phrase
        <input
          type="text"
          value={rejectPhrase}
          onChange={(e) => setRejectPhrase(e.target.value)}
          placeholder="Phrase to never use again"
        />
      </label>

      <button type="button" className="feedback-save-btn" onClick={saveCorrection} disabled={saving}>
        {saving ? "Saving…" : "Save brand preference"}
      </button>

      {message && <p className="feedback-msg">{message}</p>}

      {profile && (
        <details className="feedback-profile">
          <summary>Learned preferences</summary>
          <pre>{JSON.stringify(profile, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
