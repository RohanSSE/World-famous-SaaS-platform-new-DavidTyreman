import { useOrbPresence, ORB_STATES } from "../../context/OrbPresenceContext";
import "./OrbPresence.css";

export default function OrbPresence({ children, className = "" }) {
  const { state, thinkingStep, intelligenceLabel } = useOrbPresence();

  const stateClass = {
    [ORB_STATES.IDLE]: "orb-idle",
    [ORB_STATES.THINKING]: "orb-thinking",
    [ORB_STATES.RETRIEVING]: "orb-retrieving",
    [ORB_STATES.SPEAKING]: "orb-speaking",
    [ORB_STATES.MEMORY]: "orb-memory",
    [ORB_STATES.CONNECTING]: "orb-connecting",
  }[state] || "orb-idle";

  return (
    <div className={`orb-presence ${stateClass} ${className}`}>
      <div className="orb-presence-ring" aria-hidden />
      <div className="orb-presence-core">{children}</div>
      {thinkingStep && state !== ORB_STATES.IDLE && state !== ORB_STATES.SPEAKING && (
        <div className="orb-presence-tooltip">{thinkingStep}</div>
      )}
      {intelligenceLabel && (
        <div className="orb-intelligence-badge" title="System intelligence mode">
          {intelligenceLabel}
        </div>
      )}
    </div>
  );
}
