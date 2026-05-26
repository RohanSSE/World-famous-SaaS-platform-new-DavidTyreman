TAG = "motion"
# fix: use div
TAG = "div"

content = f'''import {{ useOrbPresence, ORB_STATES }} from "../../context/OrbPresenceContext";
import "./OrbPresence.css";

export default function OrbPresence({{ children, className = "" }}) {{
  const {{ state, thinkingStep }} = useOrbPresence();

  const stateClass = {{
    [ORB_STATES.IDLE]: "orb-idle",
    [ORB_STATES.THINKING]: "orb-thinking",
    [ORB_STATES.RETRIEVING]: "orb-retrieving",
    [ORB_STATES.SPEAKING]: "orb-speaking",
    [ORB_STATES.MEMORY]: "orb-memory",
    [ORB_STATES.CONNECTING]: "orb-connecting",
  }}[state] || "orb-idle";

  return (
    <{TAG} className={{`orb-presence ${{stateClass}} ${{className}}`}}>
      <{TAG} className="orb-presence-ring" aria-hidden />
      <{TAG} className="orb-presence-core">{{children}}</{TAG}>
      {{thinkingStep && state !== ORB_STATES.IDLE && state !== ORB_STATES.SPEAKING && (
        <{TAG} className="orb-presence-tooltip">{{thinkingStep}}</{TAG}>
      )}}
    </{TAG}>
  );
}}
'''
open(r"c:\Users\apurvu\Documents\Godfather\GodFather_frontend\src\components\orb\OrbPresence.jsx", "w", encoding="utf-8").write(content)
