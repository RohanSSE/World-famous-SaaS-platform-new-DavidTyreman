TAG = "div"
content = f'''import "./SourceCards.css";

function confidenceFromScore(score) {{
  if (score == null) return null;
  const pct = score <= 1 ? Math.round(score * 100) : Math.round(Math.min(score * 10, 100));
  return Math.min(99, Math.max(40, pct));
}}

export default function SourceCards({{ sources = [], graphConcepts = [], visible = true }}) {{
  if (!visible || (!sources.length && !graphConcepts.length)) return null;

  return (
    <{TAG} className="source-cards" aria-label="Knowledge sources">
      <{TAG} className="source-cards-header">
        <span className="source-cards-icon">*</span>
        <span>ORB connected knowledge</span>
      </{TAG}>
      {{sources.slice(0, 4).map((src, i) => {{
        const conf = confidenceFromScore(src.relevance_score);
        const title = src.title || src.document_title || src.file || "Knowledge";
        const category = src.category || "knowledge";
        return (
          <{TAG} key={{`${{title}}-${{i}}`}} className="source-card">
            <{TAG} className="source-card-top">
              <span className="source-category-chip">{{category}}</span>
              {{conf != null && (
                <span className="source-confidence">Confidence: {{conf}}%</span>
              )}}
            </{TAG}>
            <{TAG} className="source-card-title">{{title}}</{TAG}>
            {{src.file && <{TAG} className="source-card-file">{{src.file}}</{TAG}>}}
          </{TAG}>
        );
      }})}}
      {{graphConcepts.length > 0 && (
        <{TAG} className="source-graph-relations">
          <span className="source-graph-label">Related concepts</span>
          <{TAG} className="source-graph-chips">
            {{graphConcepts.map((c) => (
              <span key={{c}} className="source-graph-chip">{{c}}</span>
            ))}}
          </{TAG}>
        </{TAG}>
      )}}
    </{TAG}>
  );
}}
'''
path = r"c:\Users\apurvu\Documents\Godfather\GodFather_frontend\src\components\rag\SourceCards.jsx"
open(path, "w", encoding="utf-8").write(content)
print("written", path)
