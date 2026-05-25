"""

Agentic quality pipeline: draft → critique → detect weakness → self-repair → verify → stream.

Adaptive Strategic Reasoning with conditional multi-pass.

"""

from __future__ import annotations



import json

import logging

import time

from typing import Any, Dict, List, Optional, Tuple



from django.conf import settings



from .adaptive_repair import (

    apply_overclaim_suppression,

    build_reasoning_constraints_prompt,

    detect_critique_flags,

    run_self_repair_pass,

)

from .claim_verification import detect_unsupported_claims, verify_answer_against_context

from .brand_cognition import (
    apply_adaptive_confidence_language,
    build_inference_repair_instructions,
    should_regenerate_for_cognition,
    strict_evidence_prompt,
)
from .brand_language_anchor import apply_generic_phrase_replacements, format_language_anchor_prompt
from .grounded_generation import (
    build_claim_regeneration_instructions,
    build_grounding_constraints_prompt,
    build_hard_claim_regeneration_instructions,
    build_sentence_mirror_prompt,
    extract_context_phrases,
    rewrite_weak_claim_sentences,
    should_force_hard_claim_regen,
    should_regenerate_for_claims,
    suppress_unsupported_strategic_language,
)

from .prompt_orchestrator import load_prompt, render_prompt

from .rag_evaluation import detect_ungrounded_generic_filler, score_strategic_specificity

from .reasoning_drift import score_reasoning_drift



logger = logging.getLogger(__name__)





def _chat(client, model: str, messages: List[Dict], temperature: float, max_tokens: int, stream: bool = False):

    kwargs = {

        "model": model,

        "messages": messages,

        "temperature": temperature,

        "max_tokens": max_tokens,

    }

    if stream:

        kwargs["stream"] = True

    return client.chat.completions.create(**kwargs)





def generate_draft(

    client,

    model: str,

    messages: List[Dict[str, str]],

    temperature: float = 0.7,

    max_tokens: int = 1200,

) -> Tuple[str, Dict[str, int]]:

    completion = _chat(client, model, messages, temperature, max_tokens)

    usage = {}

    if completion.usage:

        usage = {

            "prompt_tokens": completion.usage.prompt_tokens or 0,

            "completion_tokens": completion.usage.completion_tokens or 0,

            "total_tokens": completion.usage.total_tokens or 0,

        }

    return completion.choices[0].message.content.strip(), usage





def _pass_strategic_interpretation(

    client,

    model: str,

    query: str,

    context: str,

    temperature: float = 0.3,

) -> str:

    """Pass 1 — internal strategic read (short, not returned to user)."""

    if not getattr(settings, "RAG_MULTI_PASS_REASONING", True):

        return ""

    prompt = (

        f"Query: {query}\n\nContext excerpt:\n{context[:2500]}\n\n"

        "In 2-3 sentences, state the core strategic tension and which brand book principles apply. "

        "Do not give recommendations yet."

    )

    try:

        completion = _chat(

            client,

            model,

            [{"role": "user", "content": prompt}],

            temperature,

            120,

        )

        return completion.choices[0].message.content.strip()

    except Exception as e:

        logger.debug("Strategic interpretation pass skipped: %s", e)

        return ""





def critique_draft(client, model: str, query: str, context: str, draft: str) -> Dict[str, Any]:

    template = load_prompt("quality/critique_v1.txt")

    prompt = render_prompt(template, context=context, query=query, draft=draft)

    completion = _chat(

        client,

        model,

        [{"role": "user", "content": prompt}],

        temperature=0.2,

        max_tokens=600,

    )

    raw = completion.choices[0].message.content.strip()

    try:

        return json.loads(raw)

    except json.JSONDecodeError:

        return {"improvement_instructions": raw, "groundedness": 5}





def verify_draft_llm(client, model: str, query: str, context: str, draft: str) -> Dict[str, Any]:

    template = load_prompt("quality/verify_v1.txt")

    prompt = render_prompt(template, context=context, query=query, draft=draft)

    try:

        completion = _chat(

            client,

            model,

            [{"role": "user", "content": prompt}],

            temperature=0.1,

            max_tokens=800,

        )

        raw = completion.choices[0].message.content.strip()

        if raw.startswith("```"):

            raw = raw.split("```")[1]

            if raw.startswith("json"):

                raw = raw[4:]

        return json.loads(raw)

    except Exception as e:

        logger.debug("LLM verify skipped: %s", e)

        return {}





def improve_draft(

    client,

    model: str,

    query: str,

    context: str,

    draft: str,

    critic_instructions: str,

) -> str:

    template = load_prompt("quality/improve_v1.txt")

    extra = critic_instructions

    unsupported = detect_unsupported_claims(draft, context)

    if unsupported:

        extra += "\n\nRemove or rewrite these unsupported sentences:\n"

        extra += "\n".join(
            f"- {u.get('sentence') or u.get('claim', '')}" for u in unsupported[:5]
        )

    filler = detect_ungrounded_generic_filler(draft, context)

    if filler:

        extra += "\n\nRemove generic filler NOT in retrieved knowledge:\n"

        extra += "\n".join(f"- \"{f['phrase']}\"" for f in filler[:5])

    prompt = render_prompt(

        template,

        context=context,

        query=query,

        draft=draft,

        critic_instructions=extra,

    )

    completion = _chat(

        client,

        model,

        [{"role": "user", "content": prompt}],

        temperature=0.5,

        max_tokens=1200,

    )

    return completion.choices[0].message.content.strip()





def run_quality_pipeline(

    client,

    model: str,

    messages: List[Dict[str, str]],

    query: str,

    context: str,

    temperature: float = 0.7,

    max_tokens: int = 1200,

    retrieval_confidence: str = "high_confidence",

    force_full_verify: bool = False,

    context_quality: Optional[Dict[str, Any]] = None,

    retrieval_critique: Optional[Dict[str, Any]] = None,

    confidence_score: Optional[float] = None,

    strategic_query: bool = False,

    composed_chunks: Optional[List[Dict[str, Any]]] = None,
    language_anchors: Optional[Dict[str, Any]] = None,

) -> Dict[str, Any]:

    """

    Adaptive pipeline:

    Pass1 interpret → draft → critique → detect flags → self-repair → verify → drift → overclaim suppress

    """

    t0 = time.perf_counter()

    verification_ms = 0

    context_quality = context_quality or {}

    composed_chunks = composed_chunks or []

    context_phrases = extract_context_phrases(context, composed_chunks)

    grounding_prompt = (
        strict_evidence_prompt()
        + "\n"
        + build_grounding_constraints_prompt(context_phrases=context_phrases)
        + build_sentence_mirror_prompt(context, composed_chunks)
    )
    if language_anchors:
        grounding_prompt += format_language_anchor_prompt(language_anchors)



    if not getattr(settings, "RAG_QUALITY_PIPELINE", True):

        answer, usage = generate_draft(client, model, messages, temperature, max_tokens)

        gen_ms = int((time.perf_counter() - t0) * 1000)

        verification = verify_answer_against_context(
            answer, context, chunks=composed_chunks, query=query
        )

        return {

            "answer": answer,

            "token_usage": usage,

            "pipeline": "single_pass",

            "verification": verification,

            "generation_ms": gen_ms,

            "verification_ms": 0,

        }



    # Pass 1: strategic interpretation (injected into user message context)

    interpretation = _pass_strategic_interpretation(client, model, query, context)

    pipeline_messages = list(messages)

    for i, m in enumerate(pipeline_messages):

        if m.get("role") == "system":

            pipeline_messages[i] = {

                **m,

                "content": (m.get("content") or "") + "\n\n" + grounding_prompt,

            }

            break



    if interpretation:

        for i, m in enumerate(pipeline_messages):

            if m.get("role") == "user" and "Context:" in m.get("content", ""):

                pipeline_messages[i] = {

                    **m,

                    "content": m["content"]

                    + f"\n\n[Strategic read]\n{interpretation}\n",

                }

                break



    # Pass 2: draft synthesis

    draft, usage1 = generate_draft(client, model, pipeline_messages, temperature, max_tokens)

    gen_ms = int((time.perf_counter() - t0) * 1000)



    rule_verify = verify_answer_against_context(draft, context, chunks=composed_chunks, query=query)

    drift_pre = score_reasoning_drift(draft, context)

    from .reliability_metrics import estimate_confidence_proxy, score_repair_success

    conf_before = estimate_confidence_proxy(context_quality, rule_verify, drift_pre)
    repair_meta: Dict[str, Any] = {}

    critique_flags = detect_critique_flags(

        draft,

        context,

        context_quality=context_quality,

        verification=rule_verify,

        drift=drift_pre,

        retrieval_critique=retrieval_critique,

        confidence_score=confidence_score,

        strategic_query=strategic_query,

    )



    filler_hits = detect_ungrounded_generic_filler(draft, context)

    specificity = score_strategic_specificity(draft, context, [])

    needs_full = (

        force_full_verify

        or bool(critique_flags)

        or retrieval_confidence in ("low_confidence", "moderate")

        or rule_verify.get("hallucination_flags")

        or len(filler_hits) >= 2

        or specificity < 0.28
        or should_force_hard_claim_regen(rule_verify)

    )



    t_v = time.perf_counter()

    critique: Dict[str, Any] = {}

    llm_verify: Dict[str, Any] = {}



    if needs_full:

        critique = critique_draft(client, model, query, context, draft)

        if getattr(settings, "RAG_LLM_VERIFY_ENABLED", True):

            llm_verify = verify_draft_llm(client, model, query, context, draft)

    verification_ms = int((time.perf_counter() - t_v) * 1000)



    instructions = critique.get("improvement_instructions", "")

    instructions = (
        build_grounding_constraints_prompt(context_phrases=context_phrases)
        + "\n\n"
        + build_reasoning_constraints_prompt(critique_flags)
        + "\n\n"
        + instructions
    )

    if filler_hits:

        instructions += " Replace generic filler with concepts from retrieved knowledge only."



    if rule_verify.get("force_exploratory_mode"):
        from .uncertainty_generation import generation_mode_prompt

        instructions += "\n\n" + generation_mode_prompt("exploratory", confidence_score or 0.45)

    if should_regenerate_for_cognition(rule_verify) or should_regenerate_for_claims(rule_verify):
        if should_force_hard_claim_regen(rule_verify):
            instructions = (
                build_hard_claim_regeneration_instructions(rule_verify, context_phrases)
                + "\n\n"
                + instructions
            )
        elif rule_verify.get("high_inference_count"):
            instructions = build_inference_repair_instructions(rule_verify) + "\n\n" + instructions
        else:
            instructions = (
                build_claim_regeneration_instructions(rule_verify, context_phrases)
                + "\n\n"
                + instructions
            )



    # Self-repair loop when weakness flags detected

    if critique_flags and getattr(settings, "RAG_SELF_REPAIR_ENABLED", True):

        draft, repair_meta = run_self_repair_pass(

            client, model, query, context, draft, critique_flags, temperature, max_tokens

        )

        rule_verify = verify_answer_against_context(draft, context, chunks=composed_chunks, query=query)

        critique_flags = detect_critique_flags(

            draft,

            context,

            context_quality=context_quality,

            verification=rule_verify,

            drift=score_reasoning_drift(draft, context),

            retrieval_critique=retrieval_critique,

            confidence_score=confidence_score,

            strategic_query=strategic_query,

        )



    if llm_verify.get("revised_response"):

        final = llm_verify["revised_response"].strip()

        pipeline_name = "adaptive_verify_llm_revise"

    elif needs_full and (rule_verify.get("unsupported_claims") or filler_hits or instructions):

        final = improve_draft(client, model, query, context, draft, instructions)

        pipeline_name = "adaptive_improve"

    elif retrieval_confidence == "high_confidence" and not critique_flags:

        final = draft

        pipeline_name = "adaptive_lightweight"

    else:

        final = improve_draft(client, model, query, context, draft, instructions or "Tighten grounding.")

        pipeline_name = "adaptive_verify_improve"



    # Pass 3: verification + drift + claim-level grounding

    final_verify = verify_answer_against_context(final, context, chunks=composed_chunks, query=query)

    final, sent_modified = rewrite_weak_claim_sentences(
        final, final_verify, context, composed_chunks
    )
    if sent_modified:
        final_verify = verify_answer_against_context(
            final, context, chunks=composed_chunks, query=query
        )
        pipeline_name = pipeline_name + "_sentence_mirror"

    if should_regenerate_for_cognition(final_verify) or should_regenerate_for_claims(final_verify):
        if should_force_hard_claim_regen(final_verify):
            regen_instr = build_hard_claim_regeneration_instructions(
                final_verify, context_phrases
            )
            pipeline_name = pipeline_name + "_hard_claim_regen"
        elif final_verify.get("high_inference_count"):
            regen_instr = build_inference_repair_instructions(final_verify)
            pipeline_name = pipeline_name + "_inference_regen"
        else:
            regen_instr = build_claim_regeneration_instructions(
                final_verify, context_phrases
            )
            pipeline_name = pipeline_name + "_claim_regen"
        final = improve_draft(client, model, query, context, final, regen_instr)
        final_verify = verify_answer_against_context(
            final, context, chunks=composed_chunks, query=query
        )
        final, sent_modified2 = rewrite_weak_claim_sentences(
            final, final_verify, context, composed_chunks
        )
        if sent_modified2:
            final_verify = verify_answer_against_context(
                final, context, chunks=composed_chunks, query=query
            )
            pipeline_name = pipeline_name + "_sentence_mirror2"

    final, lang_modified = suppress_unsupported_strategic_language(final, final_verify)
    if lang_modified:
        final_verify = verify_answer_against_context(final, context, chunks=composed_chunks, query=query)
        pipeline_name = pipeline_name + "_lang_suppress"

    conf_for_lang = confidence_score if confidence_score is not None else 0.65
    final, conf_modified = apply_adaptive_confidence_language(final, conf_for_lang, final_verify)
    if conf_modified:
        pipeline_name = pipeline_name + "_adaptive_confidence"

    if language_anchors:
        final, anchor_modified = apply_generic_phrase_replacements(final, language_anchors)
        if anchor_modified:
            final_verify = verify_answer_against_context(final, context, chunks=composed_chunks, query=query)
            pipeline_name = pipeline_name + "_language_anchor"



    drift_final = score_reasoning_drift(final, context)



    if drift_final.get("drift_detected") and getattr(settings, "RAG_SELF_REPAIR_ENABLED", True):

        final, repair_meta = run_self_repair_pass(

            client,

            model,

            query,

            context,

            final,

            ["reasoning_drift"],

            temperature,

            max_tokens,

        )

        final_verify = verify_answer_against_context(final, context, chunks=composed_chunks, query=query)

        drift_final = score_reasoning_drift(final, context)

        pipeline_name = "adaptive_drift_repair"



    # Overclaim suppression

    conf = confidence_score if confidence_score is not None else 0.75

    final, overclaim_modified = apply_overclaim_suppression(final, conf)

    conf_after = estimate_confidence_proxy(
        context_quality, final_verify, drift_final
    )
    repair_metrics = score_repair_success(
        drift_pre.get("reasoning_drift_score", 0),
        drift_final.get("reasoning_drift_score", 0),
        conf_before,
        conf_after,
        bool(repair_meta.get("repaired")),
        critique_flags,
        critique_flags,
    )
    repair_metrics["repaired"] = bool(repair_meta.get("repaired"))
    repair_metrics["overclaim_suppressed"] = overclaim_modified

    return {

        "answer": final,

        "draft": draft,

        "critique": critique,

        "critique_flags": critique_flags,

        "repair": repair_meta,

        "repair_metrics": repair_metrics,

        "verification": final_verify,

        "claim_verification": final_verify,

        "rule_verification": rule_verify,

        "llm_verification": llm_verify,

        "reasoning_drift": drift_final,

        "strategic_interpretation": interpretation,

        "overclaim_suppressed": overclaim_modified,

        "token_usage": dict(usage1),

        "pipeline": pipeline_name,

        "generation_ms": gen_ms,

        "verification_ms": verification_ms,

        "retrieval_confidence_mode": retrieval_confidence,

    }





def stream_draft_tokens(client, model: str, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1200):

    stream = _chat(client, model, messages, temperature, max_tokens, stream=True)

    for chunk in stream:

        if not chunk.choices:

            continue

        delta = chunk.choices[0].delta

        if hasattr(delta, "content") and delta.content:

            yield delta.content





def stream_verified_answer(answer: str, chunk_chars: int = 4):

    """Yield verified final answer in small chunks for SSE (post verify/revise)."""

    if not answer:

        return

    text = answer.strip()

    for i in range(0, len(text), chunk_chars):

        yield text[i : i + chunk_chars]


