import { useEffect, useRef, useState } from "react";

/**
 * Typewriter with blinking cursor + interrupt support
 */
export function useTypewriter(
  text,
  { speed = 18, enabled = true, onComplete, punctuationPause = 0, commaPause = 0 } = {},
) {
  const [display, setDisplay] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const timeoutRef = useRef(null);
  const indexRef = useRef(0);

  const stop = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
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
    let cancelled = false;

    stop();
    indexRef.current = 0;
    setDisplay("");

    if (!enabled || !text) {
      setDisplay(text || "");
      return undefined;
    }

    setIsTyping(true);
    const getNextDelay = (typedCharacter) => {
      if (punctuationPause && /[.!?]/.test(typedCharacter)) return punctuationPause;
      if (commaPause && /[,;:]/.test(typedCharacter)) return commaPause;
      return speed;
    };

    const typeNextCharacter = () => {
      if (cancelled) return;
      indexRef.current += 1;
      const nextDisplay = text.slice(0, indexRef.current);
      setDisplay(nextDisplay);

      if (indexRef.current >= text.length) {
        stop();
        onComplete?.();
        return;
      }

      timeoutRef.current = setTimeout(
        typeNextCharacter,
        getNextDelay(text[indexRef.current - 1]),
      );
    };

    timeoutRef.current = setTimeout(typeNextCharacter, speed);

    return () => {
      cancelled = true;
      stop();
    };
  }, [text, speed, enabled, punctuationPause, commaPause]);

  return { display, isTyping, stop, skipToEnd };
}

export default useTypewriter;
