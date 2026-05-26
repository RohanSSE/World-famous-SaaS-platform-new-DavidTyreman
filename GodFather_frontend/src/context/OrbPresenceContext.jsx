import { createContext, useCallback, useContext, useMemo, useState } from "react";

/**
 * Global ORB presence states — thinking, retrieving, speaking, memory, idle
 * Phase 15: intelligence mode from system_health
 */
const OrbPresenceContext = createContext(null);

export const ORB_STATES = {
  IDLE: "idle",
  THINKING: "thinking",
  RETRIEVING: "retrieving",
  SPEAKING: "speaking",
  MEMORY: "memory",
  CONNECTING: "connecting",
};

export function OrbPresenceProvider({ children }) {
  const [state, setState] = useState(ORB_STATES.IDLE);
  const [thinkingStep, setThinkingStep] = useState("");
  const [sources, setSources] = useState([]);
  const [graphConcepts, setGraphConcepts] = useState([]);
  const [intelligenceMode, setIntelligenceMode] = useState(null);
  const [intelligenceLabel, setIntelligenceLabel] = useState("");
  const [strategicInsights, setStrategicInsights] = useState([]);

  const setOrbIdle = useCallback(() => {
    setState(ORB_STATES.IDLE);
    setThinkingStep("");
  }, []);

  const setOrbThinking = useCallback((step = "Thinking…") => {
    setState(ORB_STATES.THINKING);
    setThinkingStep(step);
  }, []);

  const setOrbRetrieving = useCallback((step = "Retrieving knowledge…") => {
    setState(ORB_STATES.RETRIEVING);
    setThinkingStep(step);
  }, []);

  const setOrbSpeaking = useCallback(() => {
    setState(ORB_STATES.SPEAKING);
    setThinkingStep("");
  }, []);

  const setOrbMemory = useCallback((step = "ORB remembered…") => {
    setState(ORB_STATES.MEMORY);
    setThinkingStep(step);
  }, []);

  const setOrbConnecting = useCallback((step = "Connecting concepts…") => {
    setState(ORB_STATES.CONNECTING);
    setThinkingStep(step);
  }, []);

  const applySystemHealth = useCallback((health) => {
    if (!health) return;
    setIntelligenceMode(health.intelligence_mode || null);
    setIntelligenceLabel(health.intelligence_label || "");
  }, []);

  const value = useMemo(
    () => ({
      state,
      thinkingStep,
      sources,
      graphConcepts,
      intelligenceMode,
      intelligenceLabel,
      strategicInsights,
      setSources,
      setGraphConcepts,
      setStrategicInsights,
      applySystemHealth,
      setOrbIdle,
      setOrbThinking,
      setOrbRetrieving,
      setOrbSpeaking,
      setOrbMemory,
      setOrbConnecting,
    }),
    [
      state,
      thinkingStep,
      sources,
      graphConcepts,
      intelligenceMode,
      intelligenceLabel,
      strategicInsights,
      applySystemHealth,
      setOrbIdle,
      setOrbThinking,
      setOrbRetrieving,
      setOrbSpeaking,
      setOrbMemory,
      setOrbConnecting,
    ]
  );

  return (
    <OrbPresenceContext.Provider value={value}>{children}</OrbPresenceContext.Provider>
  );
}

export function useOrbPresence() {
  const ctx = useContext(OrbPresenceContext);
  if (!ctx) {
    return {
      state: ORB_STATES.IDLE,
      thinkingStep: "",
      sources: [],
      graphConcepts: [],
      intelligenceMode: null,
      intelligenceLabel: "",
      strategicInsights: [],
      setSources: () => {},
      setGraphConcepts: () => {},
      setStrategicInsights: () => {},
      applySystemHealth: () => {},
      setOrbIdle: () => {},
      setOrbThinking: () => {},
      setOrbRetrieving: () => {},
      setOrbSpeaking: () => {},
      setOrbMemory: () => {},
      setOrbConnecting: () => {},
    };
  }
  return ctx;
}

export default OrbPresenceContext;
