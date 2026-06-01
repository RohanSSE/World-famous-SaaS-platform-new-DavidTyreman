from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel


class QuestionConfig(BaseModel):
    next: Optional[str]
    phase: str
    prompt: str
    enforcement_rule: str


class QuestionRouter:
    QUESTION_SEQUENCE: Dict[str, Dict[str, Optional[str]]] = {
        "Q1": {
            "next": "Q2",
            "phase": "I",
            "prompt": "What motivated you to start this business journey in the first place? If you had to name the spirit behind it in one word or short phrase, what is it?",
            "enforcement_rule": "Reject money as final motivation. Require emotional origin and deeper purpose.",
        },
        "Q2": {
            "next": "Q3",
            "phase": "I",
            "prompt": "How do you define yourself as a founder when no services or features are mentioned?",
            "enforcement_rule": "Block service lists. Require belief, meaning, or change language.",
        },
        "Q3": {
            "next": "Q4",
            "phase": "I",
            "prompt": "Why do you believe your business deserves to be a go-to brand in your space?",
            "enforcement_rule": "Require evidence for go-to brand claim. Unsupported claims become aspiration.",
        },
        "Q4": {
            "next": "Q5",
            "phase": "I",
            "prompt": "What frustration about your market keeps repeating and should become strategic tension?",
            "enforcement_rule": "Convert complaints to strategic tension. Reject vague frustration.",
        },
        "Q5": {
            "next": "Q6",
            "phase": "II",
            "prompt": "Where are you consistently undervalued or misread, and what exactly are people getting wrong?",
            "enforcement_rule": "Force specific misinterpretation. Reject generic value complaints.",
        },
        "Q6": {
            "next": "Q7",
            "phase": "II",
            "prompt": "What common industry norm do you reject, and why does that rejection matter?",
            "enforcement_rule": "Require a concrete rejected norm. Block generic crowded-market answers.",
        },
        "Q7": {
            "next": "Q8",
            "phase": "II",
            "prompt": "What contrarian belief do you hold that a competitor would disagree with?",
            "enforcement_rule": "Belief must be disagreeable. If universally agreeable, challenge and deepen.",
        },
        "Q8": {
            "next": "Q9",
            "phase": "III",
            "prompt": "If all your products disappeared tomorrow, what core idea would still be true about your brand?",
            "enforcement_rule": "Zero-product test. Remove operational language.",
        },
        "Q9": {
            "next": "Q10",
            "phase": "III",
            "prompt": "What personal worldview or lived experience makes that idea non-negotiable for you?",
            "enforcement_rule": "Must be personally grounded. Block abstract moral statements.",
        },
        "Q10": {
            "next": "Q11",
            "phase": "III",
            "prompt": "What identity shift happened in you that changed how you lead this brand today?",
            "enforcement_rule": "Must describe concrete change in clarity, confidence, or behavior.",
        },
        "Q11": {
            "next": "Q12",
            "phase": "III",
            "prompt": "What line in the sand are you explicitly refusing to cross, no matter the pressure?",
            "enforcement_rule": "Mandatory opposition. Require explicit refusal.",
        },
        "Q12": {
            "next": "Q13",
            "phase": "IV",
            "prompt": "Which core value must be visible in your behavior, and how would someone observe it?",
            "enforcement_rule": "Values must be observable in action, not only stated.",
        },
        "Q13": {
            "next": "Q14",
            "phase": "IV",
            "prompt": "What emotional energy shifts in a room when your brand is fully present?",
            "enforcement_rule": "Must define emotional shift with specificity.",
        },
        "Q14": {
            "next": "Q15",
            "phase": "IV",
            "prompt": "Name your brand type in sharp terms. What are you distinctly, and what are you not?",
            "enforcement_rule": "Require distinctiveness. Block bland, generic descriptors.",
        },
        "Q15": {
            "next": "Q16",
            "phase": "V",
            "prompt": "Who is your ideal client, and who is explicitly not for you?",
            "enforcement_rule": "Reject everyone-language. Force exclusion and trade-off.",
        },
        "Q16": {
            "next": "Q17",
            "phase": "V",
            "prompt": "What fear does your ideal client privately carry but rarely admits out loud?",
            "enforcement_rule": "Require psychological depth and unspoken fear.",
        },
        "Q17": {
            "next": "Q18",
            "phase": "V",
            "prompt": "What specific felt state should your client leave with after working with you?",
            "enforcement_rule": "Must be emotional and specific, not generic satisfaction.",
        },
        "Q18": {
            "next": "Q19",
            "phase": "VI",
            "prompt": "What meaningful gap do competitors fail to solve that your brand is built to address?",
            "enforcement_rule": "Require competitor gap explanation with strategic relevance.",
        },
        "Q19": {
            "next": "Q20",
            "phase": "VI",
            "prompt": "Which competitive axis do you refuse to compete on, and what axis replaces it?",
            "enforcement_rule": "Must identify explicit refusal axis and replacement.",
        },
        "Q20": {
            "next": "Q21",
            "phase": "VI",
            "prompt": "Who should feel relief when excluded by your brand, and why is that healthy for positioning?",
            "enforcement_rule": "Frame exclusion as strategic clarity, not apology.",
        },
        "Q21": {
            "next": "Q22",
            "phase": "VI",
            "prompt": "What must always be true in every client experience with your brand?",
            "enforcement_rule": "Define a repeatable, testable standard.",
        },
        "Q22": {
            "next": "Q23",
            "phase": "VII",
            "prompt": "What exactly makes people talk about you after the interaction?",
            "enforcement_rule": "Must be brag-worthy and specific enough to repeat.",
        },
        "Q23": {
            "next": "Q24",
            "phase": "VII",
            "prompt": "In the future, what should others consistently say about your brand without your help?",
            "enforcement_rule": "Define external narrative with concrete language.",
        },
        "Q24": {
            "next": "Q25",
            "phase": "VII",
            "prompt": "What work will you accept and decline to stay aligned with your brand identity?",
            "enforcement_rule": "Require clear work-boundary definition.",
        },
        "Q25": {
            "next": "Q26",
            "phase": "VIII",
            "prompt": "Where are you still avoiding the hard brand decision, and what business cost does that create?",
            "enforcement_rule": "Keep response in business context; reject therapeutic abstraction.",
        },
        "Q26": {
            "next": "Q27",
            "phase": "VIII",
            "prompt": "What risk are you currently taking by continuing to play small?",
            "enforcement_rule": "Normalize discomfort; require explicit risk articulation.",
        },
        "Q27": {
            "next": "Q28",
            "phase": "VIII",
            "prompt": "What is the explicit cost of staying broadly acceptable instead of being a go-to brand?",
            "enforcement_rule": "Must state trade-off and market consequence.",
        },
        "Q28": {
            "next": "Q29",
            "phase": "VIII",
            "prompt": "What concrete commitment will you execute immediately to embody this brand direction?",
            "enforcement_rule": "Require a specific behavior or task with immediate action.",
        },
        "Q29": {
            "next": "Q30",
            "phase": "IX",
            "prompt": "On a scale of 1-10, how ready are you to operate at go-to brand level, and what holds that number back?",
            "enforcement_rule": "Use readiness score to calibrate challenge intensity and specificity.",
        },
        "Q30": {
            "next": None,
            "phase": "IX",
            "prompt": "Authority Grant: Do you explicitly consent to operating from this brand authority going forward?",
            "enforcement_rule": "Hard stop. Confirm explicit authority consent before completion.",
        },
    }

    def get_question(self, q_id: str) -> Optional[QuestionConfig]:
        raw = self.QUESTION_SEQUENCE.get(str(q_id).upper())
        if not raw:
            return None
        return QuestionConfig(**raw)

    def get_enforcement_rule(self, q_id: str) -> str:
        cfg = self.get_question(q_id)
        if not cfg:
            return ""
        return cfg.enforcement_rule

    def is_final_question(self, q_id: str) -> bool:
        return str(q_id).upper() == "Q30"

    def get_phase(self, q_id: str) -> str:
        cfg = self.get_question(q_id)
        if not cfg:
            return "I"
        return cfg.phase

    def handle_post_pass(self, session_id: str, q_id: str) -> None:
        q = str(q_id).upper()
        if q == "Q14":
            from brandgodfather.tasks import brand_type_determination_task

            brand_type_determination_task.delay(session_id=session_id)
        if q == "Q30":
            from brandgodfather.tasks import generate_BrandBook_task, manifesto_generation_task

            generate_BrandBook_task.delay(session_id=session_id)
            manifesto_generation_task.delay(session_id=session_id)
