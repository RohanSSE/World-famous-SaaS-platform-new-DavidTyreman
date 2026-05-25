import { useCallback, useEffect, useRef, useState } from "react";

/**
 * SSE RAG stream — sources → tokens → done
 * Supports AbortController for interruption.
 */
export function useRagStream() {
  const [text, setText] = useState("");
  const [sources, setSources] = useState([]);
  const [graphConcepts, setGraphConcepts] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  useEffect(() => () => abort(), [abort]);

  const stream = useCallback(
    async ({ url, body, token, onToken, onSources, onDone, onError }) => {
      abort();
      setText("");
      setSources([]);
      setGraphConcepts([]);
      setError(null);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Stream failed: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let accumulated = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "system_health") {
                onSources?.(event);
              } else if (event.type === "sources") {
                setSources(event.sources || []);
                setGraphConcepts(event.graph_concepts || []);
                onSources?.(event);
              } else if (event.type === "token") {
                accumulated += event.content || "";
                setText(accumulated);
                onToken?.(event.content, accumulated);
              } else if (event.type === "done") {
                onDone?.(accumulated, event);
              } else if (event.type === "error") {
                throw new Error(event.message || "Stream error");
              }
            } catch (parseErr) {
              if (parseErr.message?.includes("Stream")) throw parseErr;
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
          onError?.(err);
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }

      return text;
    },
    [abort, text]
  );

  return {
    text,
    sources,
    graphConcepts,
    isStreaming,
    error,
    stream,
    abort,
    setText,
  };
}

export default useRagStream;
