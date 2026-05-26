import "./TypewriterText.css";

export default function TypewriterText({
  text,
  isTyping,
  showCursor = true,
  onClick,
  className = "",
}) {
  return (
    <span
      className={`typewriter-text ${isTyping ? "is-typing" : ""} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === "Enter" && onClick() : undefined}
      title={onClick ? "Click to show full message" : undefined}
    >
      {text}
      {showCursor && isTyping && <span className="typewriter-cursor" aria-hidden />}
    </span>
  );
}
