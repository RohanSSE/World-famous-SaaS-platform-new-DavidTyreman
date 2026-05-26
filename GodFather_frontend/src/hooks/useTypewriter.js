import { useEffect, useRef, useState } from "react";

/**
 * Typewriter with blinking cursor + interrupt support
 */
export function useTypewriter(text, { speed = 18, enabled = true, onComplete } = {}) {
  const [display, setDisplay] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const intervalRef = useRef(null);
  const indexRef = useRef(0);

  const stop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsTyping(false);
  };

  const skipToEnd = () => {
    stop();
    setDisplay(text || "");
    indexRef.current = (text || "").length;
    onComplete?.();
  };

  useEffect(() => {
    stop();
    indexRef.current = 0;
    setDisplay("");

    if (!enabled || !text) {
      setDisplay(text || "");
      return undefined;
    }

    setIsTyping(true);
    intervalRef.current = setInterval(() => {
      indexRef.current += 1;
      if (indexRef.current >= text.length) {
        setDisplay(text);
        stop();
        onComplete?.();
      } else {
        setDisplay(text.slice(0, indexRef.current));
      }
    }, speed);

    return () => stop();
  }, [text, speed, enabled]);

  return { display, isTyping, stop, skipToEnd };
}

export default useTypewriter;
