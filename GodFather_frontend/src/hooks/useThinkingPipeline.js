import { useEffect, useState } from "react";

const DEFAULT_STEPS = [
  "Thinking…",
  "Understanding strategic intent…",
  "Retrieving brand knowledge…",
  "Generating strategic response…",
];

/**
 * Cycles thinking messages while waiting for AI (perceived intelligence boost)
 */
export function useThinkingPipeline(active, steps = DEFAULT_STEPS, intervalMs = 1400) {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStepIndex(0);
      return undefined;
    }
    const id = setInterval(() => {
      setStepIndex((i) => (i + 1) % steps.length);
    }, intervalMs);
    return () => clearInterval(id);
  }, [active, steps, intervalMs]);

  return active ? steps[stepIndex] : "";
}

export default useThinkingPipeline;
