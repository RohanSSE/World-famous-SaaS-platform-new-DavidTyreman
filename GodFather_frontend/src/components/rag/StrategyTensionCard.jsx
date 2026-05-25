import "./StrategyTensionCard.css";

export default function StrategyTensionCard({ insights = [], visible = true }) {
  if (!visible || !insights.length) return null;

  const high = insights.filter((i) => i.priority === "high");
  const show = high.length ? high : insights.slice(0, 1);

  return (
    <div className="strategy-tension-card" role="alert">
      <div className="strategy-tension-header">Strategy tension detected</div>
      {show.map((ins) => (
        <p key={ins.type} className="strategy-tension-message">
          {ins.message}
        </p>
      ))}
    </div>
  );
}
