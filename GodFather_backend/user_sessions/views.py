from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse           

from accounts.permissions import HasRolePermission  # Assuming this exists
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, F, Value, CharField, Case, When
from django.conf import settings
from django.db.models.functions import Round
from django.utils import timezone
from django.core.mail import send_mail
from .models import Session, Answer, Question,  ReviewComment, AIOutput, FoundationSummary
from .serializers import (
    SessionListSerializer, SessionDetailSerializer, SessionCreateSerializer, SessionCreateSingleSerializer,
    AnswerSerializer, AnswerCreateSerializer, QuestionSerializer, ReviewCommentSerializer, AIOutputSerializer,
    ConversationSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os
import re
from openai import AzureOpenAI
from reportlab.lib.colors import HexColor, Color
import json
from .models import Conversation

# Azure OpenAI only: lazy client on first use.
_openai_client = None


def get_openai_client():
    """Return Azure OpenAI client. Raises if Azure is not configured."""
    global _openai_client
    if _openai_client is None:
        from document.utils.embedding_service import _normalize_azure_endpoint

        azure_endpoint = _normalize_azure_endpoint(os.getenv('AZURE_OPENAI_ENDPOINT', ''))
        azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        if not azure_endpoint or not azure_key:
            raise ValueError(
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY to use AI features."
            )
        _openai_client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_key,
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
        )
    return _openai_client


def get_openai_chat_model():
    """Return the Azure chat model/deployment name."""
    return os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')


# ---- Structured Brand Book (heading, sub_heading, sections for UI) ----
BRAND_SUMMARY_STRUCTURE_INSTRUCTIONS = """
Respond with a single valid JSON object only (no markdown, no code fence). Use this exact shape so the UI can map and display each part:

{
  "heading": "One compelling headline that captures the brand in a line",
  "sub_heading": "One or two full sentences that capture the brand essence and emotional truth.",
    "brand_dna": [
        { "title": "USP point one", "content": "Why this is a unique selling point from the full discovery journey." },
        { "title": "USP point two", "content": "Why this is a unique selling point from the full discovery journey." },
        { "title": "USP point three", "content": "Why this is a unique selling point from the full discovery journey." }
    ],
  "sections": [
    {
      "title": "Brand Story",
      "content": "A standalone section written in clear brand-book prose.",
      "godfather_commentary": {
        "why_it_works": "One short paragraph explaining the strategic strength of this section.",
        "how_to_apply": "One short paragraph explaining how the client should use this section in decisions, messaging, sales, hiring, delivery, or content."
      }
    },
    { "title": "Big Idea", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Brand Promise", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Audience", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Vision", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Mission", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Differentiation", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Values & Behaviors", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "Voice & Tone", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } },
    { "title": "How To Use This Brand", "content": "...", "godfather_commentary": { "why_it_works": "...", "how_to_apply": "..." } }
  ]
}

Each section must be generated independently and be usable on its own. Do not write one long narrative broken into fake headings. Each section needs its own strategic point, language, and application.

Brand DNA is mandatory: generate exactly 3 points from the user's complete journey, not from one answer. Each Brand DNA point must name a distinct USP/unique selling point and explain why it makes the brand harder to copy.

Use the Vessel & Craft Brand Book reference structure when available from RAG: clear section titles, concise strategic copy, and short Brand Godfather commentary that explains why the section works and how it should be applied.

WORD COUNT (strict): heading + sub_heading + all section "content" fields combined should be between 900 and 1600 words. Each section content should be 70-140 words. Commentary fields should be 25-60 words each.

Rules: heading and sub_heading are short; each section "content" must be a rich, detailed paragraph (multiple sentences, no bullet points). Commentary must be practical and specific. Output only the JSON object.
"""


def _summary_text_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(_summary_text_value(item) for item in value if _summary_text_value(item)).strip()
    if isinstance(value, dict):
        return _summary_text_value(value.get("text") or value.get("content") or value.get("value") or "")
    return str(value).strip()


def _normalize_godfather_commentary(section):
    commentary = section.get("godfather_commentary") or section.get("brand_godfather_commentary") or section.get("commentary") or {}
    if isinstance(commentary, str):
        return {"why_it_works": commentary.strip(), "how_to_apply": ""}
    if not isinstance(commentary, dict):
        commentary = {}
    return {
        "why_it_works": _summary_text_value(
            commentary.get("why_it_works")
            or commentary.get("why")
            or commentary.get("why_this_works")
            or section.get("why_it_works")
        ),
        "how_to_apply": _summary_text_value(
            commentary.get("how_to_apply")
            or commentary.get("application")
            or commentary.get("how_it_should_be_applied")
            or section.get("how_to_apply")
        ),
    }


def _normalize_summary_section(section, fallback_title="Brand Section"):
    if not isinstance(section, dict):
        return {
            "title": fallback_title,
            "content": _summary_text_value(section),
            "godfather_commentary": {"why_it_works": "", "how_to_apply": ""},
        }
    return {
        "title": _summary_text_value(section.get("title") or section.get("heading") or fallback_title),
        "content": _summary_text_value(section.get("content") or section.get("body") or section.get("text")),
        "godfather_commentary": _normalize_godfather_commentary(section),
    }


def _normalize_brand_dna_points(points):
    if not isinstance(points, list):
        return []
    normalized = []
    for idx, point in enumerate(points[:3]):
        if isinstance(point, dict):
            title = _summary_text_value(point.get("title") or point.get("label") or point.get("usp") or f"Brand DNA {idx + 1}")
            content = _summary_text_value(point.get("content") or point.get("description") or point.get("why") or point.get("value"))
        else:
            title = f"Brand DNA {idx + 1}"
            content = _summary_text_value(point)
        if title or content:
            normalized.append({"title": title or f"Brand DNA {idx + 1}", "content": content})
    return normalized


def _parse_structured_summary(raw_text):
    """Parse AI response into { heading, sub_heading, sections }. Fallback to legacy single block if not JSON."""
    raw_text = (raw_text or "").strip()
    # Try to extract JSON if wrapped in markdown code block
    if "```" in raw_text:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start >= 0 and end > start:
            raw_text = raw_text[start:end]
    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict):
            raise TypeError("Structured summary must be a JSON object")
        heading = _summary_text_value(data.get("heading") or data.get("title"))
        sub_heading = _summary_text_value(data.get("sub_heading") or data.get("subHeading") or data.get("subtitle"))
        brand_dna = _normalize_brand_dna_points(data.get("brand_dna") or data.get("brandDNA") or data.get("dna_points"))
        sections = data.get("sections")
        if isinstance(sections, list) and len(sections) > 0:
            sections = [
                _normalize_summary_section(s, fallback_title=f"Brand Section {idx + 1}")
                for idx, s in enumerate(sections)
            ]
        else:
            sections = [_normalize_summary_section(raw_text, fallback_title="Summary")]
        return {
            "heading": heading or "Brand Book",
            "sub_heading": sub_heading or "",
            "brand_dna": brand_dna,
            "sections": sections,
        }
    except (json.JSONDecodeError, TypeError):
        return {
            "heading": "Brand Book",
            "sub_heading": "",
            "brand_dna": [],
            "sections": [_normalize_summary_section(raw_text, fallback_title="Summary")],
        }


def _split_text_chunks(text, sentence_limit=3):
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\n", " ").split(".") if p.strip()]
    chunks = []
    for i in range(0, len(parts), sentence_limit):
        seg = ". ".join(parts[i:i + sentence_limit]).strip()
        if seg and not seg.endswith("."):
            seg += "."
        if seg:
            chunks.append(seg)
    return chunks


def _build_brand_book_payload(session, summary):
    """
    Convert structured summary into deterministic multi-page brand book payload.
    UI can render this directly like the target reference design.
    """
    heading = (summary or {}).get("heading") or "Brand Overview"
    sub_heading = (summary or {}).get("sub_heading") or ""
    brand_dna = _normalize_brand_dna_points((summary or {}).get("brand_dna") or (summary or {}).get("brandDNA") or (summary or {}).get("dna_points"))
    sections = (summary or {}).get("sections") or []
    normalized_sections = [
        _normalize_summary_section(s, fallback_title=f"Brand Section {idx + 1}")
        for idx, s in enumerate(sections)
        if isinstance(s, dict) or _summary_text_value(s)
    ]

    if not normalized_sections:
        normalized_sections = [_normalize_summary_section(sub_heading or heading, fallback_title="Brand Overview")]

    def page(page_id, title, items):
        return {
            "id": page_id,
            "title": title,
            "sections": items,
        }

    section_groups = [
        ("foundation", "Strategic Foundation", normalized_sections[0:2]),
        ("promise-audience", "Promise & Audience", normalized_sections[2:4]),
        ("vision-mission", "Vision & Mission", normalized_sections[4:6]),
        ("positioning", "Positioning & Behavior", normalized_sections[6:8]),
        ("expression", "Voice & Application", normalized_sections[8:10]),
    ]

    pages = [
        {
            "id": "overview",
            "title": "Brand Overview",
            "overview_fields": [
                {"label": "Brand Name", "value": session.title or "Your Brand"},
                {"label": "Brand Book Direction", "value": heading},
                {"label": "Core Belief", "value": sub_heading or "Defined through the discovery answers."},
            ],
            "sections": [],
        }
    ]

    if brand_dna:
        pages.append({
            "id": "brand-dna",
            "title": "Brand DNA",
            "sections": [],
            "dna_points": brand_dna,
        })

    for group_id, group_title, group_sections in section_groups:
        if group_sections:
            pages.append(page(group_id, group_title, group_sections))

    if len(normalized_sections) > 10:
        pages.append(page("additional", "Additional Brand Sections", normalized_sections[10:]))

    if pages:
        pages[-1]["cta_label"] = "Explore More"

    return {
        "sidebar_title": "Brand Book",
        "brand_name": session.title or "Brand",
        "pages": pages,
    }


# Multiple Sessions
def _strategic_challenge_for_draft(question, draft: str, heuristic: dict, refined: bool = False) -> dict:
    quality = str(heuristic.get("quality") or "too_weak")
    profile = heuristic.get("profile") or {}
    step = str(profile.get("step") or profile.get("category") or "this question")
    draft_text = (draft or "").strip()
    words = len(re.findall(r"\b[\w']+\b", draft_text))

    if quality == "vendor_thought":
        challenge = (
            "This is still describing the offer, not the brand. "
            "Before we touch the wording, name the belief or behavior that makes this true.\n\n"
            "What would your best customer feel or do differently because this brand exists?"
        )
        challenge_type = "vendor_thought"
    elif quality == "too_weak" or words < 10:
        challenge = (
            f"There is a start here, but it is too safe for {step}. "
            "I am not polishing this yet; we need the truth underneath it.\n\n"
            "What are you willing to stand for that a generic competitor would avoid saying?"
        )
        challenge_type = "shallow_answer"
    else:
        challenge = (
            "This has enough shape to keep working with, but do not jump to polish first. "
            "Make the strategic choice sharper before the language gets cleaner.\n\n"
            "Who is this for, who is it not for, and what truth does that force you to own?"
        )
        challenge_type = "strategic_challenge"

    return {
        "improved_answer": draft_text,
        "follow_up_question": challenge,
        "mode": "challenge_first",
        "rewrite_blocked": True,
        "challenge_type": challenge_type,
        "quality": quality,
        "reason": heuristic.get("reason") or "Challenge the thinking before improving copy.",
        "refined_requested": bool(refined),
    }


@swagger_auto_schema(
    method='get',
    operation_description="Client task dashboard - view own session",
    responses={200: SessionDetailSerializer(), 403: "No permission"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def task_dashboard(request):
    if not request.user.has_perm_codename('sessions.view'):
        return Response({"detail": "No permission"}, status=403)

    if not request.user.has_dashboard_access('tasks'):
        return Response({"detail": "No access to this dashboard"}, status=403)
    
    user = request.user
    session = Session.objects.filter(created_by=user).first()
    
    if session:
        serializer = SessionDetailSerializer(session)
        return Response({"session": serializer.data})
    else:
        return Response({"message": "No session found. You can start a new session."})




@swagger_auto_schema(
    method='get',
    operation_description="Agency review dashboard - view assigned sessions by status",
    responses={200: openapi.Response("Sessions grouped by status with stats")}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def review_dashboard(request):
    if not request.user.has_perm_codename('sessions.view'):
        return Response({"detail": "No permission"}, status=403)
    
    if not request.user.has_dashboard_access('reviews'):
        return Response({"detail": "No access to this dashboard"}, status=403)
    
    user = request.user
    from accounts.agency_utils import ensure_agency_for_user
    agency = user.agency or (ensure_agency_for_user(user) if user.has_role('agency') else None)
    if not agency:
        return Response({"detail": "Not part of any agency"}, status=403)

    sessions = Session.objects.filter(agency=agency)
    
    sessions_with_feedback = sessions.annotate(
        pending_feedback_count=Count('review_comments', filter=Q(review_comments__is_resolved=False))
    )
    
    return Response({
        'in_progress': SessionListSerializer(sessions_with_feedback.filter(status='in_progress'), many=True).data,
        'completed': SessionListSerializer(sessions_with_feedback.filter(status='completed'), many=True).data,
        'locked': SessionListSerializer(sessions_with_feedback.filter(status='locked'), many=True).data,
        'stats': {
            'total_assigned': sessions.count(),
            'in_progress': sessions.filter(status='in_progress').count(),
            'awaiting_review': sessions.filter(status='completed').count(),
            'locked': sessions.filter(status='locked').count(),
            'with_pending_feedback': sessions_with_feedback.filter(pending_feedback_count__gt=0).count(),
        }
    })


@swagger_auto_schema(
    method='get',
    operation_description="Comprehensive agency dashboard with stats, review queue, AI alerts, client progress, and recent activities",
    responses={200: openapi.Response("Agency dashboard data")}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agency_dashboard(request):
    user = request.user

    # Agency users see their agency sessions; admins see all
    if user.is_superuser or user.has_role('admin'):
        sessions = Session.objects.all()
    elif user.has_role('agency') or user.agency_id:
        from accounts.agency_utils import ensure_agency_for_user
        from accounts.status_utils import is_user_effectively_active

        if user.has_role('agency') and not is_user_effectively_active(user):
            return Response(
                {
                    "detail": "Your agency account is pending admin approval.",
                    "code": "agency_pending_approval",
                },
                status=403,
            )
        agency = ensure_agency_for_user(user)
        if not agency:
            return Response({"detail": "Not part of any agency"}, status=403)
        sessions = Session.objects.filter(agency=agency)
    else:
        return Response({"detail": "Not part of any agency"}, status=403)

    total_questions = Question.objects.filter(is_active=True).count()

    # ── TOP CARDS ──
    assigned_clients = sessions.values('created_by').distinct().count()
    in_progress = sessions.filter(status='in_progress').count()
    pending_reviews = sessions.filter(status='completed').count()

    approved_manifestos = AIOutput.objects.filter(
        session__in=sessions, status='completed'
    ).count()

    # Weak AI sessions: sessions where answered < 50% of total questions
    weak_threshold = total_questions * 0.5 if total_questions > 0 else 0
    sessions_annotated = sessions.annotate(answer_count=Count('answers'))
    weak_ai_sessions = sessions_annotated.filter(answer_count__lt=weak_threshold).count()

    # Avg brand score: average progress across all sessions
    avg_progress = 0
    if total_questions > 0 and sessions.exists():
        total_progress = sum(
            (s.answers.count() / total_questions) * 100 for s in sessions
        )
        avg_progress = round(total_progress / sessions.count(), 1)

    # ── REVIEW QUEUE ──
    review_queue = []
    for s in sessions.filter(status__in=['in_progress', 'completed']).select_related('created_by')[:10]:
        progress = round(s.get_progress(), 1)
        needs_review = s.status == 'completed'
        has_weak = progress < 50

        issue = "Needs Review" if needs_review else ("Weak positioning" if has_weak else "In Progress")
        review_queue.append({
            'session_id': s.id,
            'client_name': s.title,
            'client_email': s.created_by.email,
            'status': s.status,
            'progress': progress,
            'issue': issue,
            'pending_comments': s.review_comments.filter(is_resolved=False).count(),
        })

    # ── AI ALERTS ──
    ai_alerts = []
    for s in sessions_annotated.select_related('created_by'):
        ans_count = s.answer_count
        if total_questions > 0:
            pct = (ans_count / total_questions) * 100
        else:
            pct = 0

        # Check specific weaknesses
        audience_qs = Question.objects.filter(is_active=True, category='target_audience')
        audience_answered = s.answers.filter(question__in=audience_qs).count()
        if audience_qs.exists() and audience_answered < audience_qs.count():
            ai_alerts.append({
                'session_id': s.id,
                'client_name': s.title,
                'alert': 'Weak audience clarity',
                'severity': 'warning',
            })

        has_manifesto = AIOutput.objects.filter(session=s, status='completed').exists()
        if pct > 70 and not has_manifesto:
            ai_alerts.append({
                'session_id': s.id,
                'client_name': s.title,
                'alert': 'Manifesto not ready',
                'severity': 'info',
            })

        messaging_qs = Question.objects.filter(is_active=True, category='messaging')
        messaging_answered = s.answers.filter(question__in=messaging_qs).count()
        if messaging_qs.exists() and messaging_answered < messaging_qs.count() * 0.5:
            ai_alerts.append({
                'session_id': s.id,
                'client_name': s.title,
                'alert': 'Inconsistent messaging',
                'severity': 'warning',
            })

    # ── CLIENT PROGRESS TRACKER ──
    client_progress = []
    stages_map = {1: 'Basic', 2: 'Foundation', 3: 'Identity', 4: 'More'}
    for s in sessions.select_related('created_by')[:20]:
        current_stage = s.get_current_stage()
        stage_label = stages_map.get(current_stage, 'Complete')
        progress = round(s.get_progress(), 1)
        client_progress.append({
            'session_id': s.id,
            'client_name': s.title,
            'client_email': s.created_by.email,
            'current_stage': stage_label,
            'current_stage_num': current_stage,
            'progress': progress,
            'status': s.status,
        })

    # ── RECENT ACTIVITIES ──
    recent_activities = []

    # Recent answers
    recent_answers = Answer.objects.filter(
        session__in=sessions
    ).select_related('session', 'question', 'answered_by').order_by('-updated_at')[:10]
    for a in recent_answers:
        recent_activities.append({
            'type': 'answer_updated',
            'message': f"{a.session.title} updated {a.question.category} answer",
            'timestamp': a.updated_at.isoformat(),
            'session_id': a.session.id,
        })

    # Recent manifestos
    recent_manifestos = AIOutput.objects.filter(
        session__in=sessions
    ).order_by('-created_at')[:5]
    for m in recent_manifestos:
        recent_activities.append({
            'type': 'manifesto_generated',
            'message': f"Manifesto generated for {m.session.title}",
            'timestamp': m.created_at.isoformat(),
            'session_id': m.session.id,
        })

    # Recent comments
    recent_comments = ReviewComment.objects.filter(
        session__in=sessions
    ).select_related('session', 'created_by').order_by('-created_at')[:5]
    for c in recent_comments:
        recent_activities.append({
            'type': 'comment_added',
            'message': f"Revision requested on {c.session.title}",
            'timestamp': c.created_at.isoformat(),
            'session_id': c.session.id,
        })

    # Sort all activities by timestamp desc
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:15]

    # ── ALL SESSIONS LIST ──
    all_sessions = SessionListSerializer(sessions, many=True).data

    return Response({
        'stats': {
            'assigned_clients': assigned_clients,
            'in_progress_projects': in_progress,
            'pending_reviews': pending_reviews,
            'approved_manifestos': approved_manifestos,
            'weak_ai_sessions': weak_ai_sessions,
            'avg_brand_score': avg_progress,
        },
        'review_queue': review_queue,
        'ai_alerts': ai_alerts[:10],
        'client_progress': client_progress,
        'recent_activities': recent_activities,
        'sessions': all_sessions,
    })


@swagger_auto_schema(
    method='get',
    operation_description="User/Client dashboard with stats, branding journey progress, AI suggestions, agency feedback, and manifesto status",
    responses={200: openapi.Response("User dashboard data")}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user
    sessions = Session.objects.filter(created_by=user)
    total_questions = Question.objects.filter(is_active=True).count()

    # ── TOP CARDS ──
    # Current brand stage (from latest session)
    latest_session = sessions.first()
    stages_map = {1: 'Basic', 2: 'Foundation', 3: 'Identity', 4: 'More'}
    current_stage = 'No Session'
    current_stage_num = 0
    completion_pct = 0
    manifesto_status = 'Not Started'

    if latest_session:
        current_stage_num = latest_session.get_current_stage()
        current_stage = stages_map.get(current_stage_num, 'Complete')
        completion_pct = round(latest_session.get_progress(), 1)

        if AIOutput.objects.filter(session=latest_session, status='completed').exists():
            manifesto_status = 'Generated'
        elif AIOutput.objects.filter(session=latest_session, status='processing').exists():
            manifesto_status = 'Processing'
        elif latest_session.is_complete():
            manifesto_status = 'Ready to Generate'
        else:
            manifesto_status = 'Pending'

    # AI quality score: average answer coverage across sessions
    ai_quality = 0
    if total_questions > 0 and sessions.exists():
        total_coverage = sum(
            (s.answers.count() / total_questions) * 100 for s in sessions
        )
        ai_quality = round(total_coverage / sessions.count(), 1)

    # Pending feedback
    pending_feedback = ReviewComment.objects.filter(
        session__in=sessions, is_resolved=False
    ).count()

    # Uploaded documents
    from document.models import Document
    uploaded_docs = Document.objects.filter(uploaded_by=user).count()

    # ── BRANDING JOURNEY PROGRESS ──
    journey_progress = []
    for s in sessions.select_related('created_by')[:10]:
        stage_num = s.get_current_stage()
        journey_progress.append({
            'session_id': s.id,
            'title': s.title,
            'current_stage': stages_map.get(stage_num, 'Complete'),
            'current_stage_num': stage_num,
            'progress': round(s.get_progress(), 1),
            'status': s.status,
        })

    # ── AI SUGGESTIONS ──
    ai_suggestions = []
    if latest_session:
        # Check audience clarity
        audience_qs = Question.objects.filter(is_active=True, category='target_audience')
        audience_answered = latest_session.answers.filter(question__in=audience_qs).count()
        if audience_qs.exists() and audience_answered < audience_qs.count():
            ai_suggestions.append({
                'type': 'warning',
                'message': 'Your audience definition is too broad. Try specifying customer age group.',
            })

        # Check messaging
        messaging_qs = Question.objects.filter(is_active=True, category='messaging')
        messaging_answered = latest_session.answers.filter(question__in=messaging_qs).count()
        if messaging_qs.exists() and messaging_answered < messaging_qs.count() * 0.5:
            ai_suggestions.append({
                'type': 'info',
                'message': 'Your messaging needs more clarity. Consider adding emotional depth.',
            })

        # Check identity
        identity_qs = Question.objects.filter(is_active=True, category='brand_identity')
        identity_answered = latest_session.answers.filter(question__in=identity_qs).count()
        if identity_qs.exists() and identity_answered < identity_qs.count():
            ai_suggestions.append({
                'type': 'info',
                'message': 'Complete your brand identity section for a stronger manifesto.',
            })

        # General progress hint
        if completion_pct < 50:
            ai_suggestions.append({
                'type': 'info',
                'message': f'You are {completion_pct}% complete. Keep going to unlock your manifesto!',
            })

    # ── AGENCY FEEDBACK ──
    agency_feedback = []
    recent_comments = ReviewComment.objects.filter(
        session__in=sessions
    ).select_related('session', 'created_by').order_by('-created_at')[:10]
    for c in recent_comments:
        agency_feedback.append({
            'session_id': c.session.id,
            'session_title': c.session.title,
            'comment': c.comment,
            'by': c.created_by.email,
            'is_resolved': c.is_resolved,
            'created_at': c.created_at.isoformat(),
        })

    # ── MANIFESTO PREVIEW ──
    manifesto_preview = None
    if latest_session:
        try:
            ai_output = AIOutput.objects.get(session=latest_session)
            manifesto_preview = {
                'session_id': latest_session.id,
                'status': ai_output.status,
                'has_content': bool(ai_output.manifesto or ai_output.json_output),
                'created_at': ai_output.created_at.isoformat(),
            }
        except AIOutput.DoesNotExist:
            pass

    # ── RECENT ACTIVITIES ──
    recent_activities = []
    recent_answers = Answer.objects.filter(
        session__in=sessions
    ).select_related('session', 'question').order_by('-updated_at')[:8]
    for a in recent_answers:
        recent_activities.append({
            'type': 'answer_updated',
            'message': f"Updated {a.question.category} answer in {a.session.title}",
            'timestamp': a.updated_at.isoformat(),
            'session_id': a.session.id,
        })

    recent_manifestos = AIOutput.objects.filter(session__in=sessions).order_by('-created_at')[:3]
    for m in recent_manifestos:
        recent_activities.append({
            'type': 'manifesto_generated',
            'message': f"Manifesto generated for {m.session.title}",
            'timestamp': m.created_at.isoformat(),
            'session_id': m.session.id,
        })

    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]

    # ── SESSIONS LIST ──
    all_sessions = SessionListSerializer(sessions, many=True).data

    return Response({
        'stats': {
            'current_stage': current_stage,
            'completion_pct': completion_pct,
            'ai_quality_score': ai_quality,
            'pending_feedback': pending_feedback,
            'uploaded_documents': uploaded_docs,
            'manifesto_status': manifesto_status,
            'total_projects': sessions.count(),
        },
        'journey_progress': journey_progress,
        'ai_suggestions': ai_suggestions,
        'agency_feedback': agency_feedback,
        'manifesto_preview': manifesto_preview,
        'recent_activities': recent_activities,
        'sessions': all_sessions,
        'latest_session_id': latest_session.id if latest_session else None,
    })


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter: draft/in_progress/completed/locked')
    ],
    responses={200: SessionListSerializer(many=True), 403: "No permission"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_list(request):
    if not request.user.has_perm_codename('sessions.view'):
        return Response({"detail": "No permission"}, status=403)
    
    user = request.user
    
    if user.is_superuser or user.has_role('admin'):
        queryset = Session.objects.all()
    elif user.has_role('agency'):
        if user.agency:
            queryset = Session.objects.filter(agency=user.agency)
        else:
            queryset = Session.objects.none()
    else:
        queryset = Session.objects.filter(created_by=user)
    
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    serializer = SessionListSerializer(queryset, many=True)
    return Response(serializer.data)


# Multiple Sessions
@swagger_auto_schema(
    method='POST',
    operation_description="Create new session",
    request_body=SessionCreateSerializer,
    responses={201: SessionDetailSerializer(), 400: "Invalid data", 403: "No permission"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_create(request):
    role_name = getattr(request.user.role, 'name', None) if request.user.role else None
    can_create = (
        request.user.is_superuser
        or request.user.has_perm_codename('sessions.create')
        or role_name in ('client', 'agency')
    )
    if not can_create:
        return Response({"detail": "No permission"}, status=403)

    serializer = SessionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    session = serializer.save(created_by=request.user, status='draft')
    
    return Response(SessionDetailSerializer(session).data, status=status.HTTP_201_CREATED)




@swagger_auto_schema(
    method='get',
    operation_description="Get session details",
    responses={200: SessionDetailSerializer(), 403: "Access denied", 404: "Not found"}
)
@swagger_auto_schema(
    method='patch',
    operation_description="Update session (partial update)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'agency': openapi.Schema(type=openapi.TYPE_INTEGER, description='Agency ID to assign'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Admin only'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Admin only')
            }
        ),
    responses={200: SessionDetailSerializer(), 400: "Invalid data", 403: "No permission"}
)
@swagger_auto_schema(
    method='delete',
    operation_description="Delete session (only draft sessions)",
    responses={204: "Deleted", 400: "Cannot delete", 403: "No permission", 404: "Not found"}
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_detail(request, pk):
    session = get_object_or_404(Session, pk=pk)
    user = request.user
    
    if not session.has_access(user):
        return Response({"detail": "Access denied"}, status=403)
    
    if request.method == 'GET':
        serializer = SessionDetailSerializer(session)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        if not request.user.has_perm_codename('sessions.update'):
            return Response({"detail": "No permission"}, status=403)
        
        allowed_fields = ['title']
        if user.has_role('admin') or user.is_superuser:
            allowed_fields.extend(['agency', 'status', 'is_active'])
        
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = SessionDetailSerializer(session, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        if not request.user.has_perm_codename('sessions.delete'):
            return Response({"detail": "No permission"}, status=403)
        
        if not session.can_delete(user):
            return Response({"detail": "Can only delete draft sessions"}, status=400)
        
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='POST',
    operation_description="Start session - change status from draft to in_progress",
    responses={200: SessionDetailSerializer(), 400: "Invalid status transition", 403: "Access denied"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_start(request, pk):
    session = get_object_or_404(Session, pk=pk)
    
    if session.created_by != request.user and not request.user.is_superuser:
        return Response({"detail": "Access denied"}, status=403)
    
    if session.status != 'draft':
        return Response({"detail": f"Cannot start from '{session.status}' status"}, status=400)
    
    session.status = 'in_progress'
    session.save()
    
    return Response(SessionDetailSerializer(session).data)


@swagger_auto_schema(
    method='POST',
    operation_description="Complete session - mark all answers done",
    responses={200: openapi.Response(description="Session completed"), 400: "Not all questions answered", 403: "Access denied"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_complete(request, pk):
    session = get_object_or_404(Session, pk=pk)
    
    if session.created_by != request.user and not request.user.is_superuser:
        return Response({"detail": "Access denied"}, status=403)
    
    if not session.is_complete():
        return Response({"detail": "Answer all required Foundation (Stage 1) questions first"}, status=400)
    
    session.status = 'completed'
    session.completed_at = timezone.now()
    session.save()
    
    return Response({
        "message": "Session completed! You can now lock the brand or generate the manifesto.",
        "session": SessionDetailSerializer(session).data
    })



@swagger_auto_schema(
    method='POST',
    operation_description="Lock session (Brand Lock)",
    responses={
        200: openapi.Response(description="Session locked"),
        400: "Invalid status",
        403: "Access denied"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_lock(request, pk):
    session = get_object_or_404(Session, pk=pk)
    
    if session.created_by != request.user and not request.user.is_superuser:
        return Response({"detail": "Only creator can lock"}, status=403)
    
    if session.status != 'completed':
        return Response({"detail": "Can only lock completed sessions"}, status=400)
    
    try:
        session.lock_session(request.user)
        return Response({
            "message": "Brand session locked successfully. Edits now require unlock.",
            "session": SessionDetailSerializer(session).data
        })
    except ValueError as e:
        return Response({"detail": str(e)}, status=400)




@swagger_auto_schema(
    method='POST',
    operation_description="Unlock session with password (client only)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['password'],
        properties={'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password to unlock')}
    ),
    responses={200: openapi.Response(description="Session unlocked"), 400: "Invalid password", 403: "Access denied"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_unlock(request, pk):
    session = get_object_or_404(Session, pk=pk)
    
    if session.created_by != request.user and not request.user.is_superuser:
        return Response({"detail": "Only creator can unlock"}, status=403)
    
    try:
        session.unlock_session(request.user)
        return Response({
            "message": "Brand session unlocked. You can now edit.",
            "session": SessionDetailSerializer(session).data
        })
    except ValueError as e:
        return Response({"detail": str(e)}, status=400)




@swagger_auto_schema(
    method='POST',
    operation_description="Assign agency user to session",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['agency_id'],
        properties={'agency_id': openapi.Schema(type=openapi.TYPE_INTEGER)}
    ),
    responses={200: openapi.Response(description="Agency assigned"), 400: "Invalid agency_id", 403: "Not authorized", 404: "User not found"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_assign_agency(request, pk):
    if not request.user.has_perm_codename('sessions.update'):
        return Response({"detail": "No permission"}, status=403)
    
    session = get_object_or_404(Session, pk=pk)
    
    if not (session.created_by == request.user or request.user.is_superuser or request.user.has_role('admin')):
        return Response({"detail": "Only creator or admin can assign"}, status=403)
    
    agency_id = request.data.get('agency_id')
    if not agency_id:
        return Response({"detail": "agency_id required"}, status=400)
    
    from accounts.models import Agency
    
    try:
        agency = Agency.objects.get(id=agency_id, is_active=True)
        session.agency = agency
        session.save()
        
        # Notify all agency members
        for member in agency.users.filter(is_active=True):
            send_mail(
                'Assigned to Branding Session',
                f'Your agency has been assigned to session: {session.title}',
                'from@example.com',
                [member.email],
                fail_silently=True,
            )
        
        return Response({
            "message": f"Agency '{agency.name}' assigned",
            "session": SessionDetailSerializer(session).data
        })
    except Agency.DoesNotExist:
        return Response({"detail": "Agency not found"}, status=404)



@swagger_auto_schema(
    method='get',
    operation_description="Get all review comments for session",
    responses={200: ReviewCommentSerializer(many=True), 403: "Access denied"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_comments(request, pk):
    session = get_object_or_404(Session, pk=pk)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    comments = session.review_comments.all()
    serializer = ReviewCommentSerializer(comments, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='POST',
    operation_description="Add review comment/feedback (agency only)",
    request_body=ReviewCommentSerializer,
    responses={201: ReviewCommentSerializer(), 403: "Not assigned to review"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_add_comment(request, pk):
    if not request.user.has_perm_codename('sessions.update'):
        return Response({"detail": "No permission"}, status=403)
    
    session = get_object_or_404(Session, pk=pk)
    
    if not session.can_review(request.user):  # Assuming can_review method exists similarly
        return Response({"detail": "Not assigned to review"}, status=403)
    
    serializer = ReviewCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    comment = serializer.save(session=session, created_by=request.user)
    
    return Response(ReviewCommentSerializer(comment).data, status=status.HTTP_201_CREATED)




@swagger_auto_schema(
    method='get',
    operation_description="Get all answers for a session",
    responses={200: AnswerSerializer(many=True), 403: "Access denied"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_answers(request, pk):
    session = get_object_or_404(Session, pk=pk)

    role_name = (request.user.get_role_name() or '').lower()
    can_view_answers = (
        request.user.has_perm_codename('answers.view')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not can_view_answers:
        return Response({"detail": "No permission"}, status=403)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    answers = session.answers.all()
    serializer = AnswerSerializer(answers, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Get all conversations for a session",
    manual_parameters=[
        openapi.Parameter('question_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Filter by question ID')
    ],
    responses={200: ConversationSerializer(many=True), 403: "Access denied"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_conversations(request, pk):
    session = get_object_or_404(Session, pk=pk)

    role_name = (request.user.get_role_name() or '').lower()
    can_view_answers = (
        request.user.has_perm_codename('answers.view')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not can_view_answers:
        return Response({"detail": "No permission"}, status=403)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    conversations = session.conversations.all()
    
    # Filter by question_id if provided
    question_id = request.query_params.get('question_id')
    if question_id:
        conversations = conversations.filter(question_id=question_id)
    
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='POST',
    operation_description="Create or update answer (upsert operation)",
    request_body=AnswerCreateSerializer,
    responses={200: AnswerSerializer(), 201: AnswerSerializer(), 403: "Session locked"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_answer_create(request, pk):
    session = get_object_or_404(Session, pk=pk)

    role_name = (request.user.get_role_name() or '').lower()
    can_submit_answer = (
        request.user.has_perm_codename('answers.create')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not can_submit_answer:
        return Response({"detail": "No permission"}, status=403)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    if not session.can_edit_answers(request.user):
        return Response({"detail": "Session is locked."}, status=403)
    
    serializer = AnswerCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    question = serializer.validated_data['question']

    # ADD STAGE VALIDATION HERE
    if not session.can_access_stage(question.stage, request.user):
        if question.stage > 1:
            return Response({
                "detail": "Please upgrade your plan to continue after Phase 1.",
                "code": "subscription_required",
                "stage": question.stage,
            }, status=402)
        return Response({
            "detail": f"Please complete Stage {session.get_current_stage()} questions first before accessing Stage {question.stage}"
        }, status=400)

    answer_text = serializer.validated_data['answer_text']
    is_ai_accepted_provided = 'is_ai_accepted' in serializer.validated_data
    is_ai_accepted = bool(serializer.validated_data.get('is_ai_accepted', False))
    ai_suggestion_text = (serializer.validated_data.get('ai_suggestion') or '').strip()

    prior_ai = None
    try:
        existing = Answer.objects.get(session=session, question=question)
        prior_ai = (existing.ai_suggestion or "").strip() or None
    except Answer.DoesNotExist:
        pass

    answer_defaults = {'answer_text': answer_text, 'answered_by': request.user}
    if is_ai_accepted_provided:
        answer_defaults['is_ai_accepted'] = is_ai_accepted
    if is_ai_accepted:
        answer_defaults['ai_suggestion'] = ai_suggestion_text or answer_text
    elif ai_suggestion_text:
        answer_defaults['ai_suggestion'] = ai_suggestion_text

    answer, created = Answer.objects.update_or_create(
        session=session,
        question=question,
        defaults=answer_defaults
    )

    feedback_result = None
    original_ai = (request.data.get("original_ai_text") or prior_ai or "").strip()
    if original_ai and answer_text.strip() and original_ai != answer_text.strip() and not answer.is_ai_accepted:
        try:
            from user_sessions.services.feedback_learning import learn_from_human_edit
            feedback_result = learn_from_human_edit(
                session.id,
                original_ai,
                answer_text.strip(),
                user=request.user,
                source="answer_save",
            )
        except Exception:
            feedback_result = None

    memory_result = None
    if answer.is_ai_accepted:
        try:
            from user_sessions.services.brand_memory import record_answer_acceptance_memory
            memory_result = record_answer_acceptance_memory(answer, user=request.user)
        except Exception:
            memory_result = None

    if not created:
        ReviewComment.objects.filter(session=session, answer=answer, is_resolved=False).update(is_resolved=True, resolved_at=timezone.now())

    payload = AnswerSerializer(answer).data
    if feedback_result and feedback_result.get("learned"):
        payload["feedback_learning"] = {
            "learned": True,
            "preferred": (feedback_result.get("feedback_delta") or {}).get("preferred_phrases", [])[:5],
            "rejected": (feedback_result.get("feedback_delta") or {}).get("rejected_phrases", [])[:5],
        }
    if memory_result and memory_result.get("recorded"):
        payload["memory"] = memory_result
    return Response(payload, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Create or update multiple answers in one request (upsert per question).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['answers'],
        properties={
            'answers': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=['question_id', 'answer_text'],
                    properties={
                        'question_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'answer_text': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    ),
    responses={200: openapi.Response('saved count and optional ids', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'saved': openapi.Schema(type=openapi.TYPE_INTEGER), 'answer_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER))})), 403: "Session locked", 400: "Validation error"},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_answers_batch(request, pk):
    """POST /api/sessions/{session_id}/answers/batch/ — upsert multiple answers."""
    session = get_object_or_404(Session, pk=pk)

    role_name = (request.user.get_role_name() or '').lower()
    can_submit_answer = (
        request.user.has_perm_codename('answers.create')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not session.has_access(request.user) and not can_submit_answer:
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    if not session.can_edit_answers(request.user):
        return Response({"detail": "Session is locked."}, status=status.HTTP_403_FORBIDDEN)

    answers_payload = request.data.get("answers")
    if not isinstance(answers_payload, list):
        return Response({"detail": "answers must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    saved_ids = []
    for item in answers_payload:
        if not isinstance(item, dict):
            continue
        qid = item.get("question_id")
        answer_text = item.get("answer_text")
        if qid is None or answer_text is None:
            continue
        try:
            question = Question.objects.get(id=qid, is_active=True)
        except Question.DoesNotExist:
            continue
        if not session.can_access_stage(question.stage, request.user):
            continue
        answer, _ = Answer.objects.update_or_create(
            session=session,
            question=question,
            defaults={"answer_text": str(answer_text).strip(), "answered_by": request.user},
        )
        saved_ids.append(answer.id)

    return Response({"saved": len(saved_ids), "answer_ids": saved_ids}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='delete',
    operation_description="Delete an answer",
    responses={204: "Deleted", 403: "Cannot delete after lock"}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, HasRolePermission])
def answer_detail(request, pk, answer_id):
    session = get_object_or_404(Session, pk=pk)

    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    answer = get_object_or_404(Answer, pk=answer_id, session=session)
    
    if not session.can_edit_answers(request.user):
        return Response({"detail": "Cannot delete from locked session"}, status=403)
    
    answer.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)




# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def question_list(request):
#     session_id = request.query_params.get('session_id')
    
#     # If no session context, return all questions
#     if not session_id:
#         queryset = Question.objects.filter(is_active=True).order_by('stage', 'order')
#         user = request.user
#         visible_questions = [q for q in queryset if q.is_visible_to(user)]
        
#         category = request.query_params.get('category')
#         if category:
#             visible_questions = [q for q in visible_questions if q.category == category]
        
#         serializer = QuestionSerializer(visible_questions, many=True)
#         return Response(serializer.data)
    
#     # With session context - apply stage logic
#     session = get_object_or_404(Session, pk=session_id)
    
#     if not session.has_access(request.user):
#         return Response({"detail": "Access denied"}, status=403)
    
#     current_stage = session.get_current_stage()
#     queryset = Question.objects.filter(is_active=True).order_by('stage', 'order')
    
#     user = request.user
#     visible_questions = [q for q in queryset if q.is_visible_to(user)]
    
#     # Group by stage
#     stages_data = {}
#     for stage_num in range(1, 6):
#         stage_questions = [q for q in visible_questions if q.stage == stage_num]
#         stages_data[f'stage_{stage_num}'] = {
#             'stage_number': stage_num,
#             'stage_name': dict(Question.STAGE_CHOICES).get(stage_num),
#             'questions': QuestionSerializer(stage_questions, many=True).data,
#             'is_unlocked': current_stage >= stage_num,
#             'is_complete': current_stage > stage_num,
#             'total_questions': len(stage_questions),
#             'answered_questions': session.answers.filter(question__in=[q.id for q in stage_questions]).count()
#         }
    
#     return Response({
#         'current_stage': current_stage,
#         'stages': stages_data
#     })
@swagger_auto_schema(
    method='get',
    operation_description="List all active questions visible to user with stage progression",
    manual_parameters=[
        openapi.Parameter('category', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        openapi.Parameter('session_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Session ID for stage checking'),
        openapi.Parameter('stage', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Requested stage number')
    ],
    responses={200: QuestionSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_list(request):
    session_id = request.query_params.get('session_id')
    force_refine = str(request.query_params.get('force_refine', '')).strip().lower() in ('1', 'true', 'yes', 'on')

    # If no session context, return all questions (admin / debug use)
    if not session_id:
        queryset = Question.objects.filter(is_active=True).order_by('stage', 'order')
        user = request.user
        visible_questions = [q for q in queryset if q.is_visible_to(user)]
        serializer = QuestionSerializer(visible_questions, many=True)
        return Response(serializer.data)

    session = get_object_or_404(Session, pk=session_id)

    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    current_stage = session.get_current_stage()
    requested_stage = request.query_params.get('stage')

    if requested_stage:
        try:
            requested_stage = int(requested_stage)
        except (TypeError, ValueError):
            return Response({"detail": "stage must be a number"}, status=400)

        if not session.can_access_stage(requested_stage, request.user):
            payload = {
                "detail": "Please upgrade your plan to continue after Phase 1.",
                "code": "subscription_required" if requested_stage > 1 else "stage_locked",
                "stage": requested_stage,
                "current_stage": current_stage,
            }
            return Response(payload, status=402 if requested_stage > 1 else 400)

        questions = Question.objects.filter(
            stage=requested_stage,
            is_active=True
        ).order_by('order')

        visible_questions = [q for q in questions if q.is_visible_to(request.user)]
        return Response({
            "stage": requested_stage,
            "stage_name": dict(Question.STAGE_CHOICES).get(requested_stage),
            "mode": "bulk",
            "questions": _serialize_user_facing_questions(visible_questions, force_refine=force_refine),
        })

    if current_stage > 1 and not session.can_access_stage(current_stage, request.user):
        return Response({
            "detail": "Please upgrade your plan to continue after Phase 1.",
            "code": "subscription_required",
            "stage": current_stage,
        }, status=402)

    # =========================
    # ✅ STAGE 1: BASIC → return ALL questions at once
    # =========================
    if current_stage == 1:
        questions = Question.objects.filter(
            stage=1,
            is_active=True
        ).order_by('order')

        user = request.user
        visible_questions = [q for q in questions if q.is_visible_to(user)]

        return Response({
            "stage": 1,
            "stage_name": "Basic",
            "mode": "bulk",  # frontend can use this to show form
            "questions": _serialize_user_facing_questions(visible_questions, force_refine=force_refine)
        })

    # =========================
    # ✅ STAGE 2,3,4 → return ONE question at a time (existing flow)
    # =========================
    answered_ids = set(session.answers.values_list('question_id', flat=True))

    stage_questions = Question.objects.filter(
        stage=current_stage,
        is_active=True
    ).order_by('order')

    visible_stage_questions = [
        question for question in stage_questions if question.is_visible_to(request.user)
    ]
    refined_stage_questions = _serialize_user_facing_questions(visible_stage_questions, force_refine=force_refine)

    next_question_data = None
    for question, question_data in zip(visible_stage_questions, refined_stage_questions):
        if question.id not in answered_ids:
            next_question_data = question_data
            break

    if not next_question_data:
        return Response({
            "detail": "No more questions in this stage",
            "stage": current_stage
        })

    return Response({
        "stage": current_stage,
        "stage_name": dict(Question.STAGE_CHOICES).get(current_stage),
        "mode": "single",  # frontend shows one question screen
        "question": next_question_data
    })





QUESTION_ADMIN_COUNTS = {
    1: 8,   # Phase 1: 8 questions
    2: 12,  # Phase 2: 12 questions
    3: 10,  # Phase 3: 10 questions
}


def _is_question_admin(user):
    # Admin users: Django staff/superuser or app role name containing "admin"
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    role_name = (getattr(getattr(user, "role", None), "name", None) or "").lower()
    return "admin" in role_name


def _serialize_user_facing_questions(questions, many=True, force_refine=False):
    from user_sessions.services.question_refinement import (
        ensure_refined_questions,
        user_facing_question_text,
    )

    question_list = ensure_refined_questions(questions if many else [questions], force=force_refine)
    data = list(QuestionSerializer(question_list, many=True).data)
    for item, question in zip(data, question_list):
        item["text"] = user_facing_question_text(question)
    return data if many else data[0]


@swagger_auto_schema(
    method="post",
    operation_description="Admin: bulk replace questions for stages 1..3",
    responses={200: "Questions updated", 400: "Bad input", 403: "Forbidden"},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasRolePermission])
def admin_questions_bulk_set(request):
    if not _is_question_admin(request.user):
        return Response(
            {"detail": "You do not have permission to modify questions."},
            status=403,
        )

    stages_payload = request.data.get("stages") or {}
    if not isinstance(stages_payload, dict):
        return Response(
            {"detail": "`stages` must be an object like {\"1\": [...], \"2\": [...]}."},
            status=400,
        )

    # Validate required stage lists exactly
    for stage_num, required_count in QUESTION_ADMIN_COUNTS.items():
        stage_key = str(stage_num)
        texts = stages_payload.get(stage_key) if stage_key in stages_payload else stages_payload.get(stage_num)
        if texts is None:
            return Response(
                {"detail": f"Missing questions for stage {stage_num}."},
                status=400,
            )
        if not isinstance(texts, list):
            return Response(
                {"detail": f"Stage {stage_num} must be a list of strings."},
                status=400,
            )
        if len(texts) != required_count:
            return Response(
                {"detail": f"Stage {stage_num} requires exactly {required_count} questions, got {len(texts)}."},
                status=400,
            )

        for i, t in enumerate(texts):
            if t is None or not str(t).strip():
                return Response(
                    {"detail": f"Stage {stage_num} question #{i + 1} cannot be empty."},
                    status=400,
                )

    from django.db import transaction

    with transaction.atomic():
        created = {}
        for stage_num in sorted(QUESTION_ADMIN_COUNTS.keys()):
            Question.objects.filter(stage=stage_num).delete()

            texts = (
                stages_payload.get(str(stage_num))
                if str(stage_num) in stages_payload
                else stages_payload.get(stage_num)
            )

            new_qs = [
                Question(
                    stage=stage_num,
                    order=idx + 1,
                    text=str(text).strip(),
                    category="other",
                    is_required=True,
                    is_active=True,
                    placeholder=None,
                    help_text=None,
                )
                for idx, text in enumerate(texts)
            ]

            created_stage = Question.objects.bulk_create(new_qs)
            created[str(stage_num)] = QuestionSerializer(created_stage, many=True).data

    return Response(
        {"detail": "Questions updated successfully.", "created": created},
        status=200,
    )


@swagger_auto_schema(
    method='POST',
    operation_description="Generate AI manifesto for completed/locked session",
    responses={200: openapi.Response(description="Manifesto generation started"), 400: "Session not ready", 403: "Access denied"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_generate_manifesto(request, pk):
    if not request.user.has_perm_codename('ai.generate'):
        return Response({"detail": "No permission"}, status=403)
    
    session = get_object_or_404(Session, pk=pk)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    if session.status not in ['completed', 'locked']:
        return Response({"detail": "Session must be completed or locked before generating manifesto"}, status=400)
    
    print("Session ", session)
    ai_output, created = AIOutput.objects.get_or_create(
        session=session,
        defaults={'status': 'pending', 'generated_by': request.user}
    )

    if not created and ai_output.status == 'completed':
        return Response({"detail": "Manifesto already generated", "ai_output": AIOutputSerializer(ai_output).data})
    
    ai_output.status = 'processing'
    ai_output.save()

    use_async = request.data.get("async", settings.AI_HEAVY_ENDPOINTS_ASYNC)
    if use_async:
        try:
            from user_sessions.tasks import generate_manifesto_task
            task = generate_manifesto_task.delay(session.pk, request.user.pk)
            return Response({
                "message": "Manifesto generation started",
                "task_id": task.id,
                "status": "processing",
                "ai_output": AIOutputSerializer(ai_output).data,
                "poll_url": f"/api/sessions/ai-tasks/{task.id}/",
            })
        except Exception as e:
            logger.warning("Celery manifesto enqueue failed, running sync: %s", e)

    from user_sessions.services.ai_generation_service import run_manifesto_generation
    gen_result = run_manifesto_generation(session.pk, request.user.pk)
    ai_output.refresh_from_db()
    if not gen_result.get("success"):
        return Response(
            {"detail": gen_result.get("error", "Generation failed"), "ai_output": AIOutputSerializer(ai_output).data},
            status=500,
        )

    response_data = {
        "message": "Manifesto generated",
        "ai_output": AIOutputSerializer(ai_output).data,
        "sources": gen_result.get("sources", []),
    }
    if session.has_pending_feedback():
        response_data["warning"] = "Pending agency feedback - consider reviewing."
    return Response(response_data)


@swagger_auto_schema(
    method='get',
    operation_description="Get generated manifesto output",
    responses={200: AIOutputSerializer(), 404: "Manifesto not generated", 403: "Access denied"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_manifesto(request, pk):
    if not request.user.has_perm_codename('ai.view'):
        return Response({"detail": "No permission"}, status=403)
    
    session = get_object_or_404(Session, pk=pk)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    try:
        ai_output = session.ai_output
        serializer = AIOutputSerializer(ai_output)
        return Response(serializer.data)
    except AIOutput.DoesNotExist:
        return Response({"detail": "Manifesto not yet generated"}, status=status.HTTP_404_NOT_FOUND)


# @swagger_auto_schema(
#     method='get',
#     operation_description="Download manifesto as PDF file",
#     responses={200: openapi.Response(description="PDF file"), 404: "Manifesto not generated"}
# )
# @api_view(['GET'])
# @permission_classes([IsAuthenticated, HasRolePermission])
# def download_manifesto_pdf(request, pk):
#     session = get_object_or_404(Session, pk=pk)
#     ai_output = getattr(session, 'ai_output', None)
    
#     if not ai_output or ai_output.status != 'completed':
#         return Response({"detail": "Manifesto not yet generated"}, status=404)
    
#     from io import BytesIO
#     from reportlab.pdfgen import canvas
#     from django.http import FileResponse

#     buffer = BytesIO()
#     p = canvas.Canvas(buffer)
    
#     lock_info = f"Locked by {session.locked_by.email} on {session.locked_at}" if session.is_locked else "Unlocked"
    
#     # Use json_output if available, otherwise fall back to manifesto text
#     if ai_output.json_output:
#         json_data = ai_output.json_output
#         p.drawString(100, 800, f"Brand Manifesto for {session.title} - {lock_info}")
#         p.drawString(100, 760, f"Brand: {json_data.get('brandName', 'N/A')}")
#         p.drawString(100, 740, f"Industry: {json_data.get('industryCategory', 'N/A')}")
#         p.drawString(100, 720, f"Core Belief: {json_data.get('coreBelief', 'N/A')[:80]}...")
#     else:
#         # Fallback to old format
#         p.drawString(100, 800, f"Brand Manifesto for {session.title} - {lock_info}")
#         p.drawString(100, 780, ai_output.manifesto[:200] + "...")
    
#     p.showPage()
#     p.save()
#     buffer.seek(0)

#     return FileResponse(buffer, as_attachment=True, filename=f"Manifesto_{session.id}.pdf")



@swagger_auto_schema(
    method='get',
    operation_description="Download manifesto as PDF file",
    responses={200: openapi.Response(description="PDF file"), 404: "Manifesto not generated"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def download_manifesto_pdf(request, pk):
    session = get_object_or_404(Session, pk=pk)
    ai_output = getattr(session, 'ai_output', None)
    
    if not ai_output or ai_output.status != 'completed':
        return Response({"detail": "Manifesto not yet generated"}, status=404)
    
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from django.http import FileResponse
    from reportlab.lib.utils import simpleSplit

    buffer = BytesIO()
    width, height = A4  # 595 x 842 points
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Color palette from CSS
    brand_navy = HexColor('#0a1727')
    brand_cyan_light = HexColor('#4fe5ff')
    brand_cyan_medium = HexColor('#1ce3ed')
    brand_cyan_border = HexColor('#19869a')
    brand_blue = HexColor('#2678b7')
    brand_cyan_pill = HexColor('#d4fdff')
    brand_cyan_pill_border = HexColor('#90e7ef')
    brand_gray = HexColor('#b1b8c4')
    white = HexColor('#ffffff')
    
    # Get JSON data with fallback
    if ai_output.json_output:
        json_data = ai_output.json_output
    elif ai_output.manifesto:
        # Fallback: try to parse manifesto as JSON
        try:
            import json
            json_data = json.loads(ai_output.manifesto)
        except:
            json_data = {}
    else:
        json_data = {}
    
    # ============= PAGE 1 =============
    
    # Background
    p.setFillColor(brand_navy)
    p.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Simulate blur circles (using semi-transparent circles)
    p.setFillColor(Color(brand_cyan_light.red, brand_cyan_light.green, brand_cyan_light.blue, alpha=0.3))
    p.setFillColor(Color(brand_blue.red, brand_blue.green, brand_blue.blue, alpha=0.3))
    
    # Header Quote (hardcoded as per design)
    p.setFillColor(white)
    p.setFont("Helvetica-Oblique", 15)
    quote_text = '"Now the real work begins — living this brand, every single day."'
    p.drawCentredString(width/2, height - 50, quote_text)
    
    # Main Title with blur effect
    title_y = height - 100
    p.setFont("Helvetica-Bold", 40)
    
    # Blur effect (draw behind with cyan color and slight offset)
    p.setFillColor(Color(brand_cyan_medium.red, brand_cyan_medium.green, brand_cyan_medium.blue, alpha=0.45))
    p.drawCentredString(width/2 + 1, title_y - 1, "BRAND MANIFESTO")
    
    # Main title
    p.setFillColor(white)
    p.drawCentredString(width/2, title_y, "BRAND MANIFESTO")
    
    # Brand Overview Section
    overview_y = height - 170
    p.setFont("Helvetica", 18)
    p.setFillColor(white)
    p.drawString(36, overview_y, "Brand Overview")
    
    # Overview Card with border
    card_y = overview_y - 140
    card_height = 160
    p.setStrokeColor(brand_cyan_border)
    p.setLineWidth(1)
    p.setFillColor(brand_navy)
    p.roundRect(36, card_y, width - 72, card_height, 13, fill=True, stroke=True)
    
    # Card content - Brand Name
    p.setFont("Helvetica", 16)
    p.setFillColor(brand_gray)
    p.drawString(56, card_y + card_height - 25, "Brand Name")
    p.setFont("Helvetica-Bold", 19)
    p.setFillColor(white)
    brand_name = json_data.get('brandName', 'N/A')
    p.drawString(56, card_y + card_height - 48, brand_name)
    
    # Industry/Category
    p.setFont("Helvetica", 16)
    p.setFillColor(brand_gray)
    p.drawString(56, card_y + card_height - 75, "Industry/Category")
    p.setFont("Helvetica-Bold", 19)
    p.setFillColor(white)
    industry = json_data.get('industryCategory', 'N/A')
    p.drawString(56, card_y + card_height - 98, industry)
    
    # Core Belief (1-line Purpose) - third row
    p.setFont("Helvetica", 16)
    p.setFillColor(brand_gray)
    p.drawString(56, card_y + card_height - 125, "Core Belief (1-line Purpose)")
    p.setFont("Helvetica-Bold", 19)
    p.setFillColor(white)
    core_belief = json_data.get('coreBelief', 'N/A')
    # Wrap if too long
    wrapped_belief = simpleSplit(core_belief, "Helvetica-Bold", 19, width - 130)
    if wrapped_belief:
        p.drawString(56, card_y +  card_height - 148, wrapped_belief[0])
    
    # Two Column Section
    two_col_y = card_y - 60
    
    # Brand Origin Story (Left - 2fr)
    origin_width = (width - 104) * 0.66  # 2fr out of 3fr total
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(brand_cyan_medium)
    p.drawString(36, two_col_y, "Brand Origin Story")
    
    p.setFont("Helvetica", 14)
    p.setFillColor(white)
    origin_story = json_data.get('originStory', 'N/A')
    wrapped_origin = simpleSplit(origin_story, "Helvetica", 14, origin_width)
    origin_text_y = two_col_y - 22
    line_count = 0
    for line in wrapped_origin:
        if origin_text_y < 200:  # Stop if reaching bottom
            break
        p.drawString(36, origin_text_y, line)
        origin_text_y -= 18
        line_count += 1
        if line_count >= 10:  # Limit lines
            break
    
    # Brand's DNA (Right - 1fr)
    dna_x = 36 + origin_width + 32  # gap is 32
    p.setFont("Helvetica-Bold", 18)
    p.setFillColor(brand_cyan_medium)
    p.drawString(dna_x, two_col_y, "Brand's DNA")
    
    # DNA Pills - get from JSON
    dna_traits = json_data.get('brandDNA', ['Bold', 'Purposeful', 'Artistic'])
    pill_y = two_col_y - 46
    pill_width = 170
    pill_height = 38
    
    for trait in dna_traits[:3]:  # Max 3 traits
        # Pill background
        p.setFillColor(brand_cyan_pill)
        p.setStrokeColor(brand_cyan_pill_border)
        p.setLineWidth(1)
        p.roundRect(dna_x, pill_y, pill_width, pill_height, 8, fill=True, stroke=True)
        
        # Pill text
        p.setFillColor(brand_navy)
        p.setFont("Helvetica", 16)
        # Capitalize first letter if needed
        trait_text = trait.capitalize() if trait else 'N/A'
        p.drawString(dna_x + 22, pill_y + 12, trait_text)
        
        pill_y -= 52
    
    # Brand's Promise
    promise_y = origin_text_y - 50 if origin_text_y < two_col_y - 100 else two_col_y - 250
    p.setFont("Helvetica-Bold", 21)
    p.setFillColor(brand_cyan_medium)
    p.drawString(36, promise_y, "Brand's Promise")
    
    p.setFont("Helvetica", 13)
    p.setFillColor(white)
    brand_promise = json_data.get('brandPromise', 'N/A')
    wrapped_promise = simpleSplit(brand_promise, "Helvetica", 13, 350)
    promise_text_y = promise_y - 20
    for line in wrapped_promise[:8]:
        if promise_text_y < 50:
            break
        p.drawString(36, promise_text_y, line)
        promise_text_y -= 18
    
    # ============= PAGE 2 =============
    p.showPage()
    
    # Background
    p.setFillColor(brand_navy)
    p.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Blur circles for page 2
    p.setFillColor(Color(brand_cyan_light.red, brand_cyan_light.green, brand_cyan_light.blue, alpha=0.3))
    p.setFillColor(Color(brand_blue.red, brand_blue.green, brand_blue.blue, alpha=0.3))
    
    page2_y = height - 50
    
    # Emotional Connection Title
    p.setFont("Helvetica-Bold", 23)
    p.setFillColor(brand_cyan_medium)
    p.drawCentredString(width/2, page2_y, "Emotional Connection")
    
    # Emotional Connection Table
    page2_y -= 35
    table_height = 120
    col_width = (width - 74) / 2
    
    # Draw table border
    p.setStrokeColor(brand_cyan_medium)
    p.setLineWidth(1.2)
    p.roundRect(36, page2_y - table_height, width - 72, table_height, 7, fill=False, stroke=True)
    
    # Vertical divider
    p.setStrokeColor(Color(brand_cyan_medium.red, brand_cyan_medium.green, brand_cyan_medium.blue, alpha=0.36))
    p.line(width/2, page2_y - table_height + 6, width/2, page2_y - 6)
    
    # Before Our Brand
    p.setFont("Helvetica", 15)
    p.setFillColor(brand_gray)
    p.drawString(52, page2_y - 25, "Before Our Brand")
    
    p.setFont("Helvetica", 13)
    p.setFillColor(white)
    before_text = json_data.get('emotionalConnectionBefore', 'N/A')
    wrapped_before = simpleSplit(before_text, "Helvetica", 13, col_width - 32)
    before_y = page2_y - 42
    for line in wrapped_before[:5]:
        p.drawString(52, before_y, line)
        before_y -= 16
    
    # After Our Brand
    p.setFont("Helvetica", 15)
    p.setFillColor(brand_gray)
    p.drawString(width/2 + 16, page2_y - 25, "After Our Brand")
    
    p.setFont("Helvetica", 13)
    p.setFillColor(white)
    after_text = json_data.get('emotionalConnectionAfter', 'N/A')
    wrapped_after = simpleSplit(after_text, "Helvetica", 13, col_width - 32)
    after_y = page2_y - 42
    for line in wrapped_after[:5]:
        p.drawString(width/2 + 16, after_y, line)
        after_y -= 16
    
    # Section Divider
    page2_y -= table_height + 25
    p.setStrokeColor(Color(brand_cyan_medium.red, brand_cyan_medium.green, brand_cyan_medium.blue, alpha=0.18))
    p.setLineWidth(1.3)
    p.line(36, page2_y, width - 36, page2_y)
    
    # Differentiation Statement
    page2_y -= 35
    p.setFont("Helvetica-Bold", 30)
    p.setFillColor(brand_cyan_medium)
    p.drawString(36, page2_y, "Differentiation Statement")
    
    page2_y -= 20
    p.setFont("Helvetica", 14)
    p.setFillColor(white)
    diff_text = json_data.get('differentiationStatement', 'N/A')
    wrapped_diff = simpleSplit(diff_text, "Helvetica", 14, 385)
    for line in wrapped_diff[:4]:
        p.drawString(36, page2_y, line)
        page2_y -= 18
    
    # Two Column Banner
    page2_y -= 72
    banner_left_width = (width - 90) * 0.5
    
    # Left side text - differentiationHighlight
    p.setFont("Helvetica", 13.5)
    p.setFillColor(white)
    diff_highlight = json_data.get('differentiationHighlight', 'Unique value proposition')
    wrapped_highlight = simpleSplit(diff_highlight, "Helvetica", 13.5, banner_left_width)
    highlight_start_y = page2_y
    for line in wrapped_highlight[:3]:
        p.drawString(36, page2_y, line)
        page2_y -= 19
    
    # Right side title (hardcoded as per design)
    right_text_x = width - 240
    right_y = highlight_start_y
    p.setFont("Helvetica-Bold", 28)
    p.setFillColor(brand_cyan_medium)
    p.drawRightString(width - 36, right_y, "Brand Style & Tone")
    p.drawRightString(width - 36, right_y - 32, "& Visual mood")
    
    # Style/Tone/Visual Three Columns
    page2_y -= 32
    col_width_3 = (width - 108) / 3
    
    # Tone of Voice
    tone_x = 54
    p.setFont("Helvetica", 15)
    p.setFillColor(brand_gray)
    p.drawString(tone_x, page2_y, "Tone of Voice")
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(white)
    tone = json_data.get('toneOfVoice', 'N/A')
    wrapped_tone = simpleSplit(tone, "Helvetica-Bold", 16, col_width_3 - 10)
    tone_y = page2_y - 18
    for line in wrapped_tone[:2]:
        p.drawString(tone_x, tone_y, line)
        tone_y -= 22
    
    # Vertical separator 1
    sep1_x = 35 + col_width_3 + 18
    dde3ff_color = HexColor('#dde3ff')
    p.setStrokeColor(Color(dde3ff_color.red, dde3ff_color.green, dde3ff_color.blue, alpha=0.52))
    p.setLineWidth(1.2)
    p.line(sep1_x, page2_y + 5, sep1_x, page2_y - 60)
    
    # Visual Mood
    visual_x = sep1_x + 18
    p.setFont("Helvetica", 15)
    p.setFillColor(brand_gray)
    p.drawString(visual_x, page2_y, "Visual Mood")
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(white)
    visual = json_data.get('visualMood', 'N/A')
    wrapped_visual = simpleSplit(visual, "Helvetica-Bold", 16, col_width_3 - 10)
    visual_y = page2_y - 18
    for line in wrapped_visual[:2]:
        p.drawString(visual_x, visual_y, line)
        visual_y -= 22
    
    # Vertical separator 2
    sep2_x = visual_x + col_width_3 + 18
    p.line(sep2_x, page2_y + 5, sep2_x, page2_y - 60)
    
    # Design Style
    design_x = sep2_x + 18
    p.setFont("Helvetica", 15)
    p.setFillColor(brand_gray)
    p.drawString(design_x, page2_y, "Design Style")
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(white)
    design = json_data.get('designStyle', 'N/A')
    wrapped_design = simpleSplit(design, "Helvetica-Bold", 16, col_width_3 - 10)
    design_y = page2_y - 18
    for line in wrapped_design[:2]:
        p.drawString(design_x, design_y, line)
        design_y -= 22
    
    # Brand Tagline Drafts
    page2_y -= 110
    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(brand_cyan_medium)
    p.drawString(36, page2_y, "Brand Tagline Drafts")
    
    # Get taglines from JSON
    taglines = json_data.get('taglines', ['Tagline 1', 'Tagline 2', 'Tagline 3'])
    p.setFont("Helvetica", 15.5)
    p.setFillColor(white)
    tagline_y = page2_y - 28
    for i, tagline in enumerate(taglines[:3], 1):
        p.drawString(36, tagline_y, f'{i}. "{tagline}"')
        tagline_y -= 24
    
    # Footer Quote (hardcoded as per design)
    p.setFont("Helvetica-Oblique", 13)
    p.setFillColor(Color(white.red, white.green, white.blue, alpha=0.93))
    footer_quote = '"This is just the beginning. Let\'s turn your brand\'s truth into action."'
    p.drawCentredString(width/2, 70, footer_quote)
    
    # Save PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"Manifesto_{session.title}_{session.id}.pdf")





@swagger_auto_schema(
    method='POST',
    operation_description="Get AI suggestion for answer",
    responses={200: AnswerSerializer(), 403: "Access denied or no permission"}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def answer_ai_suggestion(request, pk, answer_id):
    session = get_object_or_404(Session, pk=pk)
    answer = get_object_or_404(Answer, pk=answer_id, session=session)
    
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)
    
    prompt = f"Suggest an improved answer for branding question: {answer.question.text}. Current answer: {answer.answer_text}"
    response = get_openai_client().chat.completions.create(
        model=get_openai_chat_model(),
        messages=[{"role": "user", "content": prompt}]
    )
    ai_suggestion = response.choices[0].message.content.strip()
    
    answer.ai_suggestion = ai_suggestion
    answer.save()
    
    return Response(AnswerSerializer(answer).data)



# @swagger_auto_schema(
#     method='post',
#     operation_description="Get AI suggestion for a new draft answer (provide question_text and answer_text in body)",
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'question_text': openapi.Schema(type=openapi.TYPE_STRING, description="Required: The branding question"),
#             'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description="Required: Current draft answer"),
#         },
#         required=['question_text', 'answer_text']
#     ),
#     responses={
#         200: openapi.Response('Suggestion', examples={'suggest': openapi.Schema(type='string')}),
#         400: "Invalid input (question_text and answer_text required)",
#         403: "Access denied or no permission",
#         500: "AI service error"
#     }
# )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated, HasRolePermission])
# def answer_ai_suggestion_draft(request, pk):
#     if not request.user.has_perm_codename('answers.ai_suggest'):
#         return Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)
    
#     session = get_object_or_404(Session, pk=pk)
#     if not session.has_access(request.user):
#         return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
#     question_text = request.data.get('question_text', '').strip()
#     draft_text = request.data.get('answer_text', '').strip()
#     if not question_text or len(question_text) < 10 or not draft_text:
#         return Response(
#             {"detail": "question_text and answer_text are required and must be meaningful (question at least 10 chars)"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     prompt = f"Suggest an improved answer for branding question: {question_text}. Current answer: {draft_text}"
#     try:
#         response = get_openai_client().chat.completions.create(
#             model=get_openai_chat_model(),
#             messages=[{"role": "user", "content": prompt}]
#         )
#         ai_suggestion = response.choices[0].message.content.strip()
#     except OpenAIError as e:
#         return Response({"detail": f"AI suggestion failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     return Response({"suggest": ai_suggestion})





from document.models import Document
from document.utils.elasticsearch_service import ElasticsearchService
from document.utils.embedding_service import EmbeddingService
from openai import OpenAIError
import logging

from utils.retrieve_ai_knowledge import retrieve_ai_knowledge, format_knowledge_context
from brandgodfather.services.ragv2.discovery_metadata import build_discovery_metadata
from user_sessions.services.rag_service import build_combined_context_for_draft
from user_sessions.services.rag_pipeline_resolver import (
    generate_rag_response,
    get_active_pipeline_name,
    retrieve_context,
    stream_rag_response,
)
from user_sessions.services.rag_observability import should_include_debug
from user_sessions.services.rag_agents import list_agents

logger = logging.getLogger(__name__)
es_service = ElasticsearchService()
embedding_service = EmbeddingService()


@swagger_auto_schema(
    method='POST',
    operation_description="Get AI suggestion from documents for a specific question",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'question_text': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Required: The branding question"
            ),
            'answer_text': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="Optional: Current draft answer (if any)"
            ),
            'document_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="Specific document IDs to search (searches all user's documents if empty)"
            ),
            'search_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['vector', 'keyword', 'hybrid'],
                default='hybrid',
                description="Search method: 'vector' (semantic), 'keyword' (text match), or 'hybrid' (both)"
            ),
            'top_k': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                default=5,
                description="Number of relevant chunks to retrieve from documents"
            ),
            'include_draft': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                default=True,
                description="Include draft answer in the prompt for improvement"
            ),
        },
        required=['question_text']
    ),
    responses={
        200: openapi.Response(
            'AI Suggestion with context',
            examples={
                'application/json': {
                    'suggest': 'Improved answer based on documents...',
                    'sources': [
                        {
                            'document_id': 1,
                            'document_title': 'Brand Strategy Guide',
                            'page_number': 5,
                            'text': 'Relevant excerpt...',
                            'relevance_score': 0.92
                        }
                    ],
                    'context_used': True,
                    'documents_searched': 3,
                    'chunks_found': 5
                }
            }
        ),
        400: "Invalid input (question_text required)",
        403: "Access denied or no permission",
        404: "No indexed documents found",
        500: "AI service error"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def answer_ai_suggestion_from_documents(request, pk):
    """
    Generate AI suggestion based on relevant content from uploaded documents.
    Searches user's documents for relevant information and creates a comprehensive answer.
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    # Extract request parameters
    question_text = request.data.get('question_text', '').strip()
    draft_text = request.data.get('answer_text', '').strip()
    document_ids = request.data.get('document_ids', [])
    search_type = request.data.get('search_type', 'hybrid')
    top_k = request.data.get('top_k', 5)
    include_draft = request.data.get('include_draft', True)
    
    # Validation
    if not question_text or len(question_text) < 10:
        return Response(
            {"detail": "question_text is required and must be at least 10 characters"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if search_type not in ['vector', 'keyword', 'hybrid']:
        search_type = 'hybrid'
    
    # Get user's indexed documents
    documents_query = Document.objects.filter(
        uploaded_by=request.user,
        is_indexed=True
    )
    
    if document_ids:
        documents_query = documents_query.filter(id__in=document_ids)
    
    documents = list(documents_query.all())
    
    if not documents:
        return Response(
            {"detail": "No indexed documents found. Please upload and index documents first."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Generate embedding for the question (needed for vector/hybrid search)
        query_embedding = None
        if search_type in ['vector', 'hybrid']:
            query_embedding = embedding_service.generate_embedding(question_text)
        
        # Search across all selected documents
        all_results = []
        for doc in documents:
            try:
                if search_type == 'keyword':
                    results = es_service.keyword_search(
                        doc.elastic_index_name, 
                        question_text, 
                        top_k
                    )
                elif search_type == 'vector':
                    results = es_service.vector_search(
                        doc.elastic_index_name, 
                        query_embedding, 
                        top_k
                    )
                else:  # hybrid
                    results = es_service.hybrid_search(
                        doc.elastic_index_name,
                        question_text,
                        query_embedding,
                        top_k
                    )
                
                # Add document metadata to results
                for result in results:
                    result['document_id'] = doc.id
                    result['document_title'] = doc.title
                
                all_results.extend(results)
                
            except Exception as e:
                logger.error(f"Error searching document {doc.id}: {str(e)}")
                continue
        
        if not all_results:
            return Response(
                {"detail": "No relevant content found in documents for this question."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Sort by relevance and take top results
        # Note: For hybrid search, results are already scored
        top_results = all_results[:top_k * 2]  # Get more for better context
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for i, result in enumerate(top_results, 1):
            context_parts.append(
                f"[Source {i} - {result['document_title']}, Page {result.get('page_number', 'N/A')}]:\n"
                f"{result['text']}\n"
            )
            
            sources.append({
                'source_number': i,
                'document_id': result['document_id'],
                'document_title': result['document_title'],
                'page_number': result.get('page_number'),
                'text': result['text'][:200] + '...' if len(result['text']) > 200 else result['text'],
                'chunk_id': result.get('chunk_id')
            })
        
        context = "\n".join(context_parts)
        
        # Print to indicate context comes from Elasticsearch
        print("=" * 50)
        print("CONTEXT FROM ELASTICSEARCH:")
        print(f"Search type: {search_type}")
        print(f"Number of results: {len(top_results)}")
        print(f"Context length: {len(context)} characters")
        print("\nDOCUMENT CHUNKS BEING USED:")
        for source in sources:
            print(f"\n--- Source {source['source_number']} ---")
            print(f"Document ID: {source['document_id']}")
            print(f"Document Title: {source['document_title']}")
            print(f"Page Number: {source['page_number']}")
            print(f"Chunk ID: {source.get('chunk_id', 'N/A')}")
            print(f"Text: {source['text']}")
        print("=" * 50)
        
        # Build AI prompt
        if include_draft and draft_text:
            prompt = f"""You are a branding expert. Based on the following information from documents, suggest an improved, comprehensive answer.

            QUESTION:
            {question_text}

            CURRENT ANSWER:
            {draft_text}

            RELEVANT INFORMATION FROM DOCUMENTS:
            {context}

            INSTRUCTIONS:
            1. Use the document information to improve and expand the answer
            2. Ensure the answer is comprehensive and well-structured
            3. Cite information naturally (e.g., "According to the Brand Strategy Guide...")
            4. Make it specific and actionable
            5. Maintain professional tone

            Provide the improved answer:"""
        else:
            prompt = f"""You are a branding expert. Based on the following information from documents, provide a comprehensive answer.

            QUESTION:
            {question_text}

            RELEVANT INFORMATION FROM DOCUMENTS:
            {context}

            INSTRUCTIONS:
            1. Create a comprehensive answer based on the document information
            2. Structure the answer clearly with main points
            3. Cite information naturally (e.g., "According to the Brand Strategy Guide...")
            4. Make it specific and actionable
            5. Maintain professional tone

            Provide the answer:"""
        
        # Get AI suggestion
        response = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert branding consultant who provides detailed, actionable answers based on provided documentation."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        ai_suggestion = response.choices[0].message.content.strip()
        
        return Response({
            "suggest": ai_suggestion,
            "sources": sources,
            "context_used": True,
            "documents_searched": len(documents),
            "chunks_found": len(top_results),
            "search_type": search_type
        })
    
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return Response(
            {"detail": f"AI suggestion failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error in AI suggestion: {str(e)}")
        return Response(
            {"detail": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# Optional: Unified endpoint that can work with or without documents
@swagger_auto_schema(
    method='POST',
    operation_description="Get AI suggestion (optionally using documents for context)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'question_text': openapi.Schema(type=openapi.TYPE_STRING, description="Required: The branding question"),
            'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description="Optional: Current draft answer"),
            'use_documents': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False, description="Search documents for context"),
            'document_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="Specific document IDs (only if use_documents=true)"
            ),
            'search_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['vector', 'keyword', 'hybrid'], default='hybrid'),
            'top_k': openapi.Schema(type=openapi.TYPE_INTEGER, default=5),
        },
        required=['question_text']
    ),
    responses={
        200: openapi.Response('AI Suggestion'),
        400: "Invalid input",
        403: "Access denied",
        500: "AI service error"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def answer_ai_suggestion_unified(request, pk):
    """
    Unified endpoint that can work with or without document context.
    If use_documents=true, searches documents for relevant context.
    Otherwise, works like the original suggestion endpoint.
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    question_text = request.data.get('question_text', '').strip()
    use_documents = request.data.get('use_documents', False)
    
    if not question_text or len(question_text) < 10:
        return Response(
            {"detail": "question_text is required and must be at least 10 characters"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # If documents should be used, delegate to document-based endpoint logic
    if use_documents:
        return answer_ai_suggestion_from_documents(request, pk)
    else:
        # Original simple suggestion
        draft_text = request.data.get('answer_text', '').strip()
        
        if draft_text:
            prompt = f"Suggest an improved answer for branding question: {question_text}. Current answer: {draft_text}"
        else:
            prompt = f"Provide a comprehensive answer for this branding question: {question_text}"
        
        try:
            response = get_openai_client().chat.completions.create(
                model=get_openai_chat_model(),
                messages=[
                    {"role": "system", "content": "You are a branding expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            ai_suggestion = response.choices[0].message.content.strip()
            
            return Response({
                "suggest": ai_suggestion,
                "context_used": False,
                "documents_searched": 0
            })
        except OpenAIError as e:
            return Response(
                {"detail": f"AI suggestion failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# @swagger_auto_schema(
#     method='post',
#     operation_description="Get AI suggestion with context from indexed documents",
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             'question_text': openapi.Schema(type=openapi.TYPE_STRING, description="Required: The branding question"),
#             'answer_text': openapi.Schema(type=openapi.TYPE_STRING, description="Required: Current draft answer"),
#             'use_documents': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Include document context", default=True),
#             'document_ids': openapi.Schema(
#                 type=openapi.TYPE_ARRAY,
#                 items=openapi.Schema(type=openapi.TYPE_INTEGER),
#                 description="Specific document IDs to search (optional, searches all if empty)"
#             ),
#         },
#         required=['question_text', 'answer_text']
#     ),
#     responses={
#         200: openapi.Response('Suggestion with context', examples={'suggest': openapi.Schema(type='string')}),
#         400: "Invalid input",
#         403: "Access denied or no permission",
#         500: "AI service error"
#     }
# )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated, HasRolePermission])
# def answer_ai_suggestion_draft(request, pk):
#     if not request.user.has_perm_codename('answers.ai_suggest'):
#         return Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)
    
#     session = get_object_or_404(Session, pk=pk)
#     if not session.has_access(request.user):
#         return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
#     question_text = request.data.get('question_text', '').strip()
#     draft_text = request.data.get('answer_text', '').strip()
#     use_documents = request.data.get('use_documents', True)
#     document_ids = request.data.get('document_ids', [])
    
#     if not question_text or len(question_text) < 10 or not draft_text:
#         return Response(
#             {"detail": "question_text and answer_text are required and must be meaningful"},
#             status=status.HTTP_400_BAD_REQUEST
#         )
    
#     context = ""
    
#     # Retrieve context from documents if enabled
#     if use_documents:
#         try:
#             # Get user's documents
#             documents_query = Document.objects.filter(
#                 uploaded_by=request.user,
#                 is_indexed=True
#             )
            
#             if document_ids:
#                 documents_query = documents_query.filter(id__in=document_ids)
            
#             documents = documents_query.all()
            
#             if documents:
#                 # Generate embedding for the question
#                 query_embedding = embedding_service.generate_embedding(question_text)
                
#                 all_results = []
#                 for doc in documents:
#                     results = es_service.hybrid_search(
#                         doc.elastic_index_name,
#                         question_text,
#                         query_embedding,
#                         top_k=3
#                     )
#                     all_results.extend(results)
                
#                 # Format context from search results
#                 if all_results:
#                     context = "\n\nRelevant context from documents:\n"
#                     for i, result in enumerate(all_results[:5], 1):
#                         context += f"{i}. {result['text']}\n"
        
#         except Exception as e:
#             logger.error(f"Error retrieving document context: {str(e)}")
#             # Continue without context rather than failing
    
#     # Build prompt with context
#     prompt = f"""Based on the following information, suggest an improved answer for the branding question.

# Question: {question_text}
# Current Answer: {draft_text}
# {context}

# Please provide a comprehensive, well-structured improved answer that incorporates relevant context."""
    
#     try:
#         response = get_openai_client().chat.completions.create(
#             model=get_openai_chat_model(),
#             messages=[
#                 {"role": "system", "content": "You are a branding expert helping to improve answers to branding questions."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )
#         ai_suggestion = response.choices[0].message.content.strip()
        
#         return Response({
#             "suggest": ai_suggestion,
#             "context_used": bool(context),
#             "documents_searched": len(documents) if use_documents and documents else 0
#         })
    
#     except OpenAIError as e:
#         return Response(
#             {"detail": f"AI suggestion failed: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

# create cache active if not active then create with question id & user id


# @swagger_auto_schema(
#     method='post',
#     operation_description="Get AI suggestion for a new draft answer (provide question_text and answer_text in body)",
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             "session_id"
#             "question_id"
#             'draft': openapi.Schema(type=openapi.TYPE_STRING, description="Required: Current draft answer"),
#         },
#         required=['question_text', 'answer_text']
#     ),
#     responses={
#         200: openapi.Response('Suggestion', examples={'suggest': openapi.Schema(type='string')}),
#         400: "Invalid input (question_text and answer_text required)",
#         403: "Access denied or no permission",
#         500: "AI service error"
#     }
# )
# @api_view(['POST'])
# @permission_classes([IsAuthenticated, HasRolePermission])  # Assuming HasRolePermission is defined elsewhere
# def answer_ai_suggestion_draft(request, pk):
#     # if request.methos == "get":
#     #      question_id = Answer.object.get(question___id = question_id)
         
#     if not request.user.has_perm_codename('answers.ai_suggest'):
#         return Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)

#     session = get_object_or_404(Session, pk=pk)
#     if not session.has_access(request.user):
#         return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

#     question_text = request.data.get('question_text', '').strip()
#     draft_text = request.data.get('answer_text', '').strip()

#     if not question_text or len(question_text) < 10 or not draft_text:
#         return Response(
#             {"detail": "question_text and answer_text are required and must be meaningful"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     context = ""

#     # Always search ALL indexed documents and build context
#     try:
#         documents_query = Document.objects.filter(is_indexed=True)
#         documents_count = documents_query.count()

#         if documents_count > 0:
#             # Use iterator to avoid loading all docs into memory if many
#             documents = documents_query.iterator(chunk_size=100)

#             query_embedding = embedding_service.generate_embedding(question_text)

#             all_results = []

#             for doc in documents:
#                 try:
#                     results = es_service.hybrid_search(
#                         doc.elastic_index_name,
#                         question_text,
#                         query_embedding,
#                         top_k=3
#                     )
#                     # Annotate with source info for context
#                     for r in results:
#                         r["_source_document_title"] = doc.title
#                     all_results.extend(results)
#                 except Exception:
#                     logger.exception("Failed search in %s", doc.elastic_index_name)

#             # Format context from top results (include doc title as mentioned in results)
#             if all_results:
#                 # Sort by score descending if available
#                 try:
#                     all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
#                 except Exception:
#                     pass

#                 context = "\n\nRelevant document context:\n"
#                 for i, result in enumerate(all_results[:5], 1):
#                     text = result.get("text", "")
#                     title = result.get("_source_document_title", "Unknown")
#                     context += f"{i}. {text} (from: {title})\n"
                
#                 print("context ", context)
#     except Exception as e:
#         logger.error("Document retrieval error: %s", str(e))
#         # Continue with empty context if search fails

#     #get active conversation history  [{"assitant":"question"}, {"user":"draft"}, {"assistant":"assitant_ans"}, {"assistant":"folloup"},{"user":"draft"},]
#     # Conversation.object.create(session=session_id, question_id=question_id, role="user", content=draft)
#     foundation = Answer.object.get(session=session_id, question_id=question_id)
#     #foundation make in array question and answer foundation_list = []
#     conversation = Conversation.object.get(session=session_id, question_id=question_id)
#     #conversation make in array question and answer conversation_list = []
#     question = Question.objects.get(pk = question_id)

#     prompt = f"""
#     You are a world-class brand strategist.
    
#     QUESTION: {question.text}
#     CURRENT ANSWER: {draft}

#     RELEVANT CONTEXT (use only if helpful):
#     {context or "None"}
#     foundation:{foundation_list}
#     conversation:{conversation_list}
#     TASK:
#     1. Rewrite the answer to be clearer, more powerful, and more brand-defining — keep the exact same tone and intent.
#     2. Then give **exactly ONE** deep, generic follow-up question that pushes the user to reveal richer insights.

#     Return ONLY this JSON (nothing else):

#     {{
#     "improved_answer": "string",
#     "follow_up_question": "single powerful question here"
#     }}
#     """

#     try:
#         resp = get_openai_client().chat.completions.create(
#             model=get_openai_chat_model(),
#             messages=[
#                 {"role": "system", "content": "Always respond in perfect JSON."},
#                 {"role": "user",   "content": prompt}
#             ],
#             response_format={"type": "json_object"},
#             temperature=0.7,
#             max_tokens=800
#         )

#         data = json.loads(resp.choices[0].message.content.strip())
#         suggest = data.get("improved_answer", draft_text)
#         follow = data.get("follow_up_question", "Can you tell us more about that?").strip(),
#         Conversation.object.create(session=session_id, question_id=question_id, role="user", content=suggest)
#         Conversation.object.create(session=session_id, question_id=question_id, role="assitant", content=follow)

#         return Response({
#             "improved_answer": suggest,
#             "follow_up_question": follow,
#             "documents_searched": documents_count,
#             "context_used": bool(context)
#         })

#     except OpenAIError as e:
#         return Response(
#             {"detail": f"AI suggestion failed: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )






@swagger_auto_schema(
    method='POST',
    operation_description="Get challenge-first coaching: exact answer copy + one strategic follow-up question",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "question_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the question"),
            "draft": openapi.Schema(type=openapi.TYPE_STRING, description="User's current draft answer"),
        },
        required=["question_id", "draft"]
    ),
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "improved_answer": openapi.Schema(type=openapi.TYPE_STRING),
                    "follow_up_question": openapi.Schema(type=openapi.TYPE_STRING),
                    "mode": openapi.Schema(type=openapi.TYPE_STRING),
                    "rewrite_blocked": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    "challenge_type": openapi.Schema(type=openapi.TYPE_STRING),
                    "quality": openapi.Schema(type=openapi.TYPE_STRING),
                    "documents_searched": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "context_used": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                }
            )
        ),
        400: "Invalid input",
        403: "Access denied",
        404: "Question not found",
        500: "AI service error",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def answer_ai_suggestion_draft(request, pk):
    """
    URL: POST /api/sessions/<pk>/ai-suggest/
    pk = session_id (from URL)
    Body: { "question_id": 5, "draft": "Our brand is about quality..." }
    """
    # 1. Session access
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    # 2. Input validation
    question_id = request.data.get("question_id")
    draft = request.data.get("draft", "").strip()
    refined = bool(request.data.get("refined"))

    if not question_id or not draft:
        return Response({"detail": "question_id and draft are required"}, status=status.HTTP_400_BAD_REQUEST)

    # 3. Get Question (global, same ID across sessions)
    try:
        question = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return Response({"detail": "Question not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
    
    
    question_text = question.text.strip()
    print("question_text ", question_text)

    from user_sessions.services.answer_quality import score_answer_quality

    heuristic = score_answer_quality(question, draft)
    challenge_payload = _strategic_challenge_for_draft(question, draft, heuristic, refined=refined)
    Conversation.objects.create(session=session, question=question, role="user", content=draft.strip())
    Conversation.objects.create(session=session, question=question, role="assistant", content=challenge_payload["follow_up_question"].strip())
    return Response({
        **challenge_payload,
        "documents_searched": 0,
        "context_used": False,
        "sources": [],
        "graph_concepts": [],
        "evaluation": None,
    }, status=status.HTTP_200_OK)

    # 4. RAG context (user docs scoped to request.user + ai_knowledge)
    rag_sources = []
    rag_graph_concepts = []
    documents_searched = 0
    context = ""
    try:
        rag_bundle = build_combined_context_for_draft(
            question_text,
            draft,
            request.user,
            session=session,
            top_k=8,
            embedding_service=embedding_service,
            es_service=es_service,
        )
        context = rag_bundle["context"]
        rag_sources = rag_bundle["sources"]
        rag_graph_concepts = rag_bundle.get("graph_concepts") or []
        documents_searched = rag_bundle["documents_searched"]
    except Exception as e:
        logger.error("Context retrieval failed: %s", e)
    # 5. Conversation history for THIS session + THIS question
    history_qs = Conversation.objects.filter(session=session, question=question).order_by('created_at')
    history_messages = [
        {"role": "assistant" if c.role == "assistant" else "user", "content": c.content}
        for c in history_qs
    ]

    print("history_messages ", history_messages)

    # 6. Optional: Foundation answer
    foundation = ""
    try:
        foundation_obj = Answer.objects.get(session=session, question=question)
        foundation = foundation_obj.answer_text.strip()
        print("foundation ", foundation)
    except Answer.DoesNotExist:
        pass

    # 7. Get brand profile from OTHER questions' final answers
    # (Current question has its own conversation, but we need context from others)
    other_questions_answers = Answer.objects.filter(
        session=session
    ).exclude(question=question).select_related('question').order_by('question__stage', 'question__order')

    brand_profile_parts = []
    for ans in other_questions_answers:
        brand_profile_parts.append(f"Q: {ans.question.text}\nA: {ans.answer_text}")

    brand_profile_summary = "\n\n".join(brand_profile_parts) if brand_profile_parts else "No previous answers from other questions yet"

    # 8. Build prompt
    
    if not refined:
    # 🚦 MODE 1 — Follow-Up Only (ZERO rewriting)
        task_block = """
    TASK — Follow-Up Only (NO rewriting):

    "improved_answer" must be an EXACT copy of the user's draft.

    WHEN THE ANSWER IS MEANINGFUL:
    Inside "follow_up_question", you MUST structure your message as THREE paragraphs:

    PARAGRAPH 1 —  APPRECIATION
    • 1–2 short sentences
    • Celebrate the identity/emotional idea they expressed
    • Direct, confident belief — not soft compliments
    • Max 1–2 emojis used meaningfully

    <blank line required>

    PARAGRAPH 2 —  SUGGESTIONS
    • 2–4 short sentences
    • Give practical identity coaching:
    - Ask for behavior that PROVES the feeling is real
    - Suggest stronger, more vivid emotional wording (Weak → Strong)
    - Provide tiny examples of how it shows up “in the room”
    • Explain why the change matters — brand must be FELT, not described

    <blank line required>

    PARAGRAPH 3 —  ONE GUIDING QUESTION
    • ONE short question (10–15 words max)
    • Must fit the question type (emotion/values/tone/promise)
    • Push one level deeper into behavior or emotional clarity
    • Conversational, not corporate

    WHEN THE ANSWER IS NONSENSE:
    • Light playful tease + one simple request to answer properly

    TONE:
    • Confident, warm, bold, slightly cheeky 😎
    • Zero corporate jargon (“leverage, ensure, implement, utilize…”)
    • Speak like a strategist who refuses generic answers

    📌 REQUIRED OUTPUT — JSON ONLY:
    {
    "improved_answer": "exact same as CURRENT DRAFT",
    "follow_up_question": "3-paragraph message"
    }
    """
    else:
        # 🚦 MODE 2 — Refine + Follow-Up
        task_block = """
    TASK — Refine & Follow-Up:

    Rewrite (“improved_answer”) to be clearer, more emotional, and identity-driven —
    without changing their meaning or adding new promises.

    Inside "follow_up_question", you MUST structure your message as THREE paragraphs:

    PARAGRAPH 1 — ⭐ APPRECIATION
    • 1–2 short sentences
    • Recognize the identity they’re growing into
    • Strong, direct tone — one emoji max here if helpful

    <blank line required>

    PARAGRAPH 2 — 🧭 SUGGESTIONS
    • 2–4 short sentences
    • Give specific, actionable coaching:
    - Behavior-based proof or example
    - Weak → Strong word upgrades
    - How to make the emotional impact VIVID
    • Explain WHY the upgrade matters — unforgettable > nice

    <blank line required>

    PARAGRAPH 3 — ❓ ONE GUIDING QUESTION
    • ONE question, 10–15 words max
    • Push deeper into the transformation or real-life behavior
    • Simple human language

    TONE:
    • Bold, direct, supportive — strategist energy
    • Minimal emojis, only to reinforce belief 🙌
    • Push away from safe, generic answers every turn

    📌 REQUIRED OUTPUT — JSON ONLY:
    {
    "improved_answer": "clearer, stronger rewrite",
    "follow_up_question": "3-paragraph message"
    }
    """


    prompt = f"""
    🎩 ROLE:
    You are THE BRAND GODFATHER — world-class brand strategist.
    Your purpose: reveal the truth of the brand — not decorate it.

    🧠 CORE PRINCIPLES:
    • Brands must be FELT — emotion > explanation
    • Behavior proves words — no behavior = wrong word
    • Specific > vague, vivid > generic, bold > safe
    • You believe in them more than they believe in themselves 😎

    🚫 FORBIDDEN (never accept these without coaching):
    “quality”, “professional”, “innovative”, “best service”, “creative”, “inspiring”, “helpful”, “reliable”
    → if any appear, suggest stronger, behavior-backed wording

    MENTAL CHECK BEFORE RESPONDING:
    1) What emotional truth are they expressing?
    2) What behavior could prove it instantly?
    3) How do I push them one level deeper right now?

    OUTPUT MUST:
    • Always be JSON only
    • Always include 2 keys: improved_answer + follow_up_question
    • follow_up_question must be EXACT 3-paragraph format:
    - Paragraph 1: Appreciation
    - Paragraph 2: Suggestions
    - Paragraph 3: ONE guiding question

    CONTEXT:
    Current question: {question_text}
    User answer: {draft}
    Foundation (if any): {foundation or "None"}
    Brand Profile: {brand_profile_summary}
    History: {json.dumps(history_messages, ensure_ascii=False, indent=2) if history_messages else "None"}
    KB context: {context or "None"}

    🔥 NON-NEGOTIABLE:
    • Push into truth every turn
    • Celebrate courage — but don’t let them hide
    • Add Minimal emojis which will be visible at least — used like seasoning, not like confetti
    • Never speak in corporate tone
    • You are building a world-famous brand with them — act like it

    {task_block}
    """




    # 9. Call OpenAI
    try:
        david_system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.

CORE RULES:
1. Base ALL responses on the provided document excerpts (David's teachings)
2. Speak in bold, direct, no-jargon tone
3. Use stories and examples from the excerpts when available
4. Never give generic marketing advice — every response must reflect David's philosophy
5. If document context is provided, you MUST use it

DAVID'S PHILOSOPHY:
• A brand is a promise KEPT, not made
• Brands must be FELT — emotion beats explanation
• Behavior proves words — no behavior = wrong word
• Specific > vague, vivid > generic, bold > safe

Respond only with perfect JSON."""

        completion = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {"role": "system", "content": david_system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200,
        )

        result = json.loads(completion.choices[0].message.content.strip())
        improved = result.get("improved_answer", draft).strip()
        follow_up = result.get("follow_up_question", "Can you tell me more?").strip()

        # Print AI suggestion result
        print("=" * 50)
        print("AI SUGGESTION RESULT:")
        print(f"Improved Answer: {improved}")
        print(f"Follow-up Question: {follow_up}")
        print("=" * 50)

        # 10. Save as natural conversation flow
        Conversation.objects.create(session=session, question=question, role="user", content=improved.strip())
        Conversation.objects.create(session=session, question=question, role="assistant", content=follow_up.strip())

        evaluation = {}
        if context and improved:
            from user_sessions.services.rag_evaluation import evaluate_rag_response

            evaluation = evaluate_rag_response(
                improved,
                context,
                rag_sources,
                [],
                query=f"{question_text} {draft}".strip(),
            )

        return Response({
            "improved_answer": improved,
            "follow_up_question": follow_up,
            "documents_searched": documents_searched,
            "context_used": bool(context),
            "sources": rag_sources,
            "graph_concepts": rag_graph_concepts,
            "evaluation": evaluation or None,
        }, status=status.HTTP_200_OK)

    except json.JSONDecodeError:
        logger.error("AI returned invalid JSON")
        return Response({"detail": "AI response was malformed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except OpenAIError as e:
        logger.exception("OpenAI error")
        return Response({"detail": "AI service temporarily unavailable"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("Unexpected error in AI suggestion")
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='POST',
    operation_description="RAG query: retrieve knowledge + GPT answer with source citations",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'query': openapi.Schema(type=openapi.TYPE_STRING),
            'include_user_docs': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
        },
        required=['query'],
    ),
    responses={200: openapi.Response(description="answer + sources")},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def rag_query(request, pk=None):
    """
    POST /api/sessions/rag-query/  or  /api/sessions/<pk>/rag-query/
    Phase 1–3: retrieval → GPT with citations.
    """
    role_name = (request.user.get_role_name() or '').lower()
    can_use_ai_suggestions = (
        request.user.has_perm_codename('answers.ai_suggest')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not can_use_ai_suggestions:
        return Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.rag_rate_limit import check_rate_limit
    allowed, remaining = check_rate_limit(request.user.id, "rag_query")
    if not allowed:
        return Response(
            {"detail": "Rate limit exceeded. Try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    user_query = (request.data.get("query") or "").strip()
    if not user_query:
        return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = None
    session_id = None
    conversation_messages = request.data.get("conversation_messages") or []
    if pk is not None:
        session = get_object_or_404(Session, pk=pk)
        session_id = session.pk
        if not session.has_access(request.user):
            return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    try:
        result = generate_rag_response(
            user_query,
            user=request.user,
            session=session,
            pipeline=str(request.data.get("pipeline") or "").strip() or None,
            agent_id=request.data.get("agent_id", "strategist"),
            include_user_docs=bool(request.data.get("include_user_docs")),
            conversation_messages=conversation_messages,
            session_summary=request.data.get("session_summary"),
            include_debug=should_include_debug(request),
            include_evaluation=bool(request.data.get("include_evaluation")),
            embedding_service=embedding_service,
            es_service=es_service,
            session_id=session_id,
        )
        payload = {
            "answer": result["answer"],
            "sources": result["sources"],
            "context_used": result["context_used"],
            "chunks_retrieved": result.get("chunks_retrieved", 0),
            "cached": result.get("cached", False),
            "agent_id": result.get("agent_id"),
            "pipeline": result.get("pipeline"),
            "graph_concepts": result.get("graph_concepts", []),
            "thinking_messages": result.get("thinking_messages", []),
            "reasoning_chain": result.get("reasoning_chain", []),
            "planner": result.get("planner"),
            "selected_agents": result.get("selected_agents", []),
            "system_health": result.get("system_health"),
            "strategic_insights": result.get("strategic_insights", []),
            "retrieval_confidence": result.get("retrieval_confidence"),
            "confidence": result.get("confidence"),
            "reasoning_trace": result.get("reasoning_trace"),
            "reasoning_path": result.get("reasoning_path"),
            "strategic_consistency": result.get("strategic_consistency"),
            "critique_flags": result.get("critique_flags"),
            "verification": result.get("verification"),
            "latency_breakdown": result.get("latency_breakdown"),
            "evaluation": result.get("evaluation"),
            "retrieval_debug": result.get("retrieval_debug"),
            "active_pipeline": result.get("active_pipeline"),
            "rag_phase": result.get("rag_phase"),
            "phase_artifact": result.get("phase_artifact"),
            "phase_artifacts": result.get("phase_artifacts", {}),
            "rate_limit_remaining": remaining,
        }
        if session is not None:
            payload["discovery_metadata"] = build_discovery_metadata(
                session_id=str(getattr(session, "session_id", session.pk)),
                q_id=f"Q{int(getattr(session, 'current_stage', 1) or 1)}",
                raw_answer=user_query,
            )
        if "debug" in result:
            payload["debug"] = result["debug"]
        return Response(payload, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("rag_query failed")
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _strategic_quote_fallback(role_name, context, phase_id):
    role = (role_name or "user").lower()
    ctx = (context or "phase_intro").lower()
    is_agency = role == "agency"

    if ctx == "phase_intro" and int(phase_id or 1) <= 1:
        text = "Before a brand can stand apart, it has to tell the truth about what it is here to become."
    elif ctx == "phase_complete":
        text = "A stronger brand does not simply move forward; it carries a clearer reason for being chosen."
    elif ctx in ("brand_book_loading", "brand_book_page"):
        text = "A Brand Book is not a document. It is the discipline that keeps meaning from drifting."
    elif ctx in ("brand_book_ready", "output_mode"):
        text = "The brand is the experience people remember after the transaction is over."
    else:
        text = "Strong brands turn scattered answers into a point of view people can feel."

    if is_agency:
        text = text.replace("brand", "agency brand", 1) if "brand" in text.lower() else text
        lens = "agency"
    else:
        lens = "user"

    return {
        "text": text,
        "author": "The Brand Godfather",
        "source": "fallback",
        "evidence": f"Generated from {lens} journey context fallback.",
    }


@swagger_auto_schema(
    method='POST',
    operation_description="Generate a contextual strategic quote for a session transition or Brand Book moment",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "context": openapi.Schema(type=openapi.TYPE_STRING, description="phase_intro, phase_complete, brand_book_loading, brand_book_page, brand_book_ready, output_mode"),
            "phase_id": openapi.Schema(type=openapi.TYPE_INTEGER),
            "source_text": openapi.Schema(type=openapi.TYPE_STRING, description="Current page or local summary text for alignment"),
        },
    ),
    responses={200: openapi.Response(description="Strategic quote")},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def strategic_quote(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    context = (request.data.get("context") or "phase_intro").strip()[:60]
    try:
        phase_id = max(1, min(3, int(request.data.get("phase_id") or 1)))
    except (TypeError, ValueError):
        phase_id = 1
    source_text = (request.data.get("source_text") or "").strip()[:1800]
    role_name = (request.user.get_role_name() or "user").lower()
    active_pipeline = get_active_pipeline_name()

    answers = Answer.objects.filter(session=session).select_related("question").order_by("question__stage", "question__order")
    answer_lines = []
    for answer in answers[:30]:
        question_text = (answer.question.text or "").strip()
        answer_text = (answer.answer_text or "").strip()
        if answer_text:
            answer_lines.append(f"Q: {question_text}\nA: {answer_text}")
    qa_text = "\n\n".join(answer_lines)[:4500]

    summary_text = ""
    try:
        summary_obj = FoundationSummary.objects.filter(session=session, status="completed").first()
        summary_text = (summary_obj.summary_text or "")[:1800] if summary_obj else ""
    except Exception:
        summary_text = ""

    rag_context = ""
    rag_sources = []
    try:
        retrieval = retrieve_context(
            f"strategic quote {context} phase {phase_id} role {role_name} {session.title} {source_text[:300]}",
            user=request.user,
            session=session,
            session_id=session.id,
            include_knowledge=True,
            agent_id="strategist",
            top_k=4,
            max_chars=2200,
        )
        active_pipeline = retrieval.get("active_pipeline") or active_pipeline
        rag_context = str(retrieval.get("context") or "").strip()[:2200]
        rag_sources = retrieval.get("sources") or []
    except Exception as e:
        logger.warning("Strategic quote RAG failed session=%s: %s", session.id, e)

    fallback = _strategic_quote_fallback(role_name, context, phase_id)
    role_lens = (
        "agency operator, client trust, portfolio growth, strategic authority"
        if role_name == "agency"
        else "founder, business owner, emotional identity, customer meaning"
    )
    context_lens = {
        "phase_intro": "before questions begin; invite self-knowledge and honesty",
        "phase_complete": "between phases; mark a strategic shift without sounding motivational",
        "brand_book_loading": "during Brand Book generation; reflection, synthesis, meaning",
        "brand_book_page": "inside Brand Book; interpret the specific page direction",
        "brand_book_ready": "before Output Mode; prepare the user to use the brand as an operating system",
        "output_mode": "Output Mode; growth and execution grounded in the Brand Book",
    }.get(context, "strategic transition")

    system_prompt = """You are THE BRAND GODFATHER.
Generate one original strategic quote for this exact user moment.

Rules:
- Do not quote famous people.
- Do not sound decorative, motivational, generic, or cheesy.
- Make it philosophical, emotionally intelligent, and strategically useful.
- If the role is agency, make the quote feel like agency/client-growth strategy.
- If the role is user/client, make the quote feel like founder/business brand identity strategy.
- Ground it in the supplied answers, summary, page text, or RAG context when available.
- Return JSON only.

JSON shape:
{
  "text": "one original quote, 8-24 words",
  "author": "The Brand Godfather",
  "evidence": "short explanation of what signal this quote was aligned to"
}
"""
    user_prompt = f"""
Role: {role_name}
Role lens: {role_lens}
Context: {context}
Context lens: {context_lens}
Phase: {phase_id}
Session title: {session.title}

Current page/source text:
{source_text or "None"}

Stored answer gist:
{qa_text or "No answers yet. Use session title, role, phase, and context."}

Stored summary:
{summary_text or "None"}

RAG context:
{rag_context or "None"}
"""

    try:
        client = get_openai_client()
        model = get_openai_chat_model()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.55,
            max_tokens=240,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content.strip()
        parsed = json.loads(raw)
        text = str(parsed.get("text") or "").strip().strip('"')
        author = str(parsed.get("author") or "The Brand Godfather").strip()
        evidence = str(parsed.get("evidence") or "Generated from session strategy signals.").strip()
        if len(text.split()) < 4 or len(text) > 180:
            raise ValueError("Generated quote failed length gate")
        return Response({
            "text": text,
            "author": author,
            "source": "llm",
            "evidence": evidence,
            "role": role_name,
            "context": context,
            "phase_id": phase_id,
            "active_pipeline": active_pipeline,
            "sources": rag_sources,
        })
    except Exception as e:
        logger.warning("Strategic quote generation failed session=%s: %s", session.id, e)
        return Response({
            **fallback,
            "role": role_name,
            "context": context,
            "phase_id": phase_id,
            "active_pipeline": active_pipeline,
            "sources": rag_sources,
        })


@swagger_auto_schema(
    method='POST',
    operation_description="RAG query with SSE token streaming (Phase 9)",
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def rag_query_stream(request, pk=None):
    """POST — Server-Sent Events stream: sources → tokens → done."""
    role_name = (request.user.get_role_name() or '').lower()
    can_use_ai_suggestions = (
        request.user.has_perm_codename('answers.ai_suggest')
        or request.user.is_superuser
        or role_name in ('admin', 'client', 'agency')
    )
    if not can_use_ai_suggestions:
        return Response({"detail": "No permission"}, status=status.HTTP_403_FORBIDDEN)

    user_query = (request.data.get("query") or "").strip()
    if not user_query:
        return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = None
    if pk is not None:
        session = get_object_or_404(Session, pk=pk)
        if not session.has_access(request.user):
            return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    def event_stream():
        try:
            for event in stream_rag_response(
                user_query,
                user=request.user,
                session=session,
                pipeline=str(request.data.get("pipeline") or "").strip() or None,
                agent_id=request.data.get("agent_id", "strategist"),
                include_user_docs=bool(request.data.get("include_user_docs")),
                conversation_messages=request.data.get("conversation_messages"),
                embedding_service=embedding_service,
                es_service=es_service,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@swagger_auto_schema(method='GET', operation_description="List ORB multi-agent definitions")
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rag_agents_list(request):
    """GET /api/sessions/rag-agents/"""
    return Response({"agents": list_agents()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rag_system_health(request):
    """GET /api/sessions/rag-system-health/ — observable RAG stack status."""
    from user_sessions.services.system_health import get_system_health

    return Response(get_system_health())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_cost_dashboard(request):
    """GET /api/sessions/ai-cost-dashboard/?days=1 — production AI cost metrics."""
    if not (request.user.is_superuser or getattr(request.user, "has_role", lambda r: False)("admin")):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.ai_cost_dashboard import get_ai_cost_dashboard

    days = int(request.query_params.get("days", 1))
    return Response(get_ai_cost_dashboard(days=days))


@swagger_auto_schema(
    method='GET',
    operation_description="Poll Celery AI task status (manifesto, summary, etc.)",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_task_status(request, task_id):
    """GET /api/sessions/ai-tasks/<task_id>/"""
    from celery.result import AsyncResult

    result = AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
    }
    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            payload["error"] = str(result.result)
    return Response(payload)


@swagger_auto_schema(
    method='POST',
    operation_description="Generate comprehensive Brand Book (structured for UI: heading, sub_heading, sections)",
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "summary": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="Structured summary for UI formatting",
                        properties={
                            "heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sub_heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sections": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                                        "content": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                )
                            ),
                        }
                    ),
                    "total_questions_answered": openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        ),
        400: "No answers found",
        403: "Access denied",
        404: "Session not found",
        500: "AI service error",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_generate_summary(request, pk):
    """
    POST /api/sessions/<pk>/generate-summary/
    
    Generates a comprehensive Brand Book from all answered questions.
    Only passes question and answer text to the prompt.
    """
    # 1. Session access check
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    # 2. Get all answers with questions (efficient query)
    answers = Answer.objects.filter(
        session=session
    ).select_related('question').order_by('question__order')
    
    if not answers.exists():
        return Response(
            {"detail": "No answers found. Please complete some questions first."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 3. Build simple Q&A text (no stage info)
    qa_text = ""
    qa_pairs = []
    
    for answer in answers:
        question_text = answer.question.text.strip()
        answer_text = answer.answer_text.strip()
        
        qa_text += f"Q: {question_text}\n"
        qa_text += f"A: {answer_text}\n\n"
        
        qa_pairs.append({
            'question': question_text,
            'answer': answer_text
        })
    
    # 4. Build prompt: structured output (heading, sub_heading, sections) for UI mapping
    prompt = f"""
🎩 ROLE:
You are THE BRAND GODFATHER — world-class brand strategist.
Your purpose: synthesize the brand's essence from all their answers into a structured summary.

🧠 CORE PRINCIPLES:
• Brands must be FELT — emotion > explanation
• Behavior proves words — no behavior = wrong word
• Specific > vague, vivid > generic, bold > safe
• Look for patterns, emotional truths, and authentic identity

TASK:
Analyze all questions and answers below. Write in full sentences and paragraphs (no bullet lists in section content). Fill:

1. **heading**: One compelling headline that captures the brand in a line.
2. **sub_heading**: One or two sentences that capture the brand essence and emotional truth.
3. **sections**: Five sections, each with a short "title" and a detailed "content" paragraph (roughly 80–140 words per section):
   - Core Themes: emotional truths and values that emerge — be specific and substantive.
   - Brand Identity: authentic brand personality, voice, and how it shows up — in full prose.
   - Key Insights: most powerful or unique aspects — with depth and examples.
   - Patterns & Truths: recurring themes, emotions, or behaviors and what they reveal.
   - The Essence: what the brand is really about at its core — synthesize in a full paragraph.

WORD COUNT: The total summary (heading + sub_heading + all five section contents) must be between 400 and 700 words. Minimum 400, maximum 700. Make each section rich and detailed so the reader gets a comprehensive picture.

TONE: Bold, direct, insightful. Reveal the brand's truth in narrative prose.

QUESTIONS & ANSWERS:

{qa_text}
"""
    
    use_async = request.data.get("async", settings.AI_HEAVY_ENDPOINTS_ASYNC)
    if use_async:
        try:
            from user_sessions.tasks import generate_session_summary_task
            task = generate_session_summary_task.delay(session.pk, request.user.pk)
            return Response({
                "message": "Summary generation started",
                "task_id": task.id,
                "status": "processing",
                "poll_url": f"/api/sessions/ai-tasks/{task.id}/",
            })
        except Exception as e:
            logger.warning("Celery summary enqueue failed, running sync: %s", e)

    from user_sessions.services.ai_generation_service import run_session_summary_generation
    gen_result = run_session_summary_generation(session.pk, request.user.pk)
    if gen_result.get("success"):
        summary_payload = gen_result["summary"] if isinstance(gen_result.get("summary"), dict) else _parse_structured_summary(gen_result.get("summary") or "")
        brand_book = _build_brand_book_payload(session, summary_payload)
        return Response({
            "summary": summary_payload,
            "brand_book": brand_book,
            "total_questions_answered": gen_result["total_questions_answered"],
            "sources": gen_result.get("sources", []),
            "brand_book_reference_sources": gen_result.get("brand_book_reference_sources", []),
        }, status=status.HTTP_200_OK)
    return Response(
        {"detail": gen_result.get("error", "Generation failed")},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@swagger_auto_schema(
    method='POST',
    operation_description="Generate social media content from session Q&A",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "platform": openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['instagram', 'facebook', 'linkedin', 'all'],
                default='all',
                description="Target platform(s) for content"
            ),
            "content_days": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                default=30,
                description="Number of days for content calendar (7, 14, or 30)"
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "brand_voice": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "social_captions": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)  # array of objects
                    ),
                    "post_ideas": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)  # array of objects
                    ),
                    "reel_scripts": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)  # array of objects
                    ),
                    "story_content": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "hashtags": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "content_calendar": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "total_answers_used": openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        ),
        400: "No answers found",
        403: "Access denied",
        500: "AI service error",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_generate_social_content(request, pk):
    """
    POST /api/sessions/<pk>/generate-social-content/
    
    Generates comprehensive social media content from session Q&A:
    - Brand voice guide
    - Social media captions
    - Post ideas
    - Reel scripts
    - Story content (questions, polls)
    - Hashtags
    - Content calendar (7/14/30-day plan)
    """
    # 1. Session access check
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
    
    # 2. Get request parameters
    platform = request.data.get('platform', 'all')
    content_days = request.data.get('content_days', 30)
    
    # Validate content_days
    if content_days not in [7, 14, 30]:
        content_days = 30
    
    # 3. Get all answers with questions
    answers = Answer.objects.filter(
        session=session
    ).select_related('question').order_by('question__order')
    
    if not answers.exists():
        return Response(
            {"detail": "No answers found. Please complete some questions first."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 4. Build Q&A text
    qa_text = ""
    for answer in answers:
        qa_text += f"Q: {answer.question.text.strip()}\n"
        qa_text += f"A: {answer.answer_text.strip()}\n\n"

    memory_context = ""
    try:
        from user_sessions.services.brand_memory import format_memory_context_block
        memory_context = format_memory_context_block(
            session.id,
            "social content generation brand voice guidance",
            agent_id="content",
            limit=4,
        )
    except Exception:
        memory_context = ""
    
    # 5. Build comprehensive prompt
    prompt = f"""
🎩 ROLE:
You are a world-class social media strategist and content creator.
Your task: Transform brand Q&A into ready-to-use social media content.

🧠 CORE PRINCIPLES:
• Content must match brand voice and personality
• Create engaging, authentic, and valuable content
• Mix educational, promotional, and engagement content
• Use platform-specific best practices
• Include clear CTAs (Call-to-Actions)

TASK:
Based on the brand Q&A below, generate comprehensive social media content.

BRAND Q&A:
{qa_text}

ACCEPTED BRAND MEMORY / GUIDANCE:
{memory_context or "No accepted brand memory recorded yet."}

REQUIRED OUTPUT (JSON format):
{{
  "brand_voice": {{
    "tone": "Professional/Friendly/Bold/etc.",
    "personality": "Description of brand personality",
    "values": ["value1", "value2", "value3"],
    "messaging_style": "How the brand communicates",
    "target_audience": "Who they're speaking to"
  }},
  "social_captions": [
    {{
      "type": "educational|promotional|engagement|brand_story|trust",
      "caption": "Full caption text (150-300 words)",
      "hook_line": "First line that grabs attention",
      "cta": "Call to action",
      "hashtags": ["#hashtag1", "#hashtag2"]
    }}
  ],
  "post_ideas": [
    {{
      "title": "Post idea title",
      "description": "What to post",
      "content_type": "carousel|single_image|video|reel",
      "suggested_caption": "Brief caption idea"
    }}
  ],
  "reel_scripts": [
    {{
      "title": "Reel title/topic",
      "hook": "First 3 seconds hook",
      "script": "Full script with timing notes",
      "visual_ideas": "What to show",
      "caption": "Reel caption",
      "hashtags": ["#hashtag1"]
    }}
  ],
  "story_content": {{
    "questions": [
      "Question for Instagram Stories",
      "Another question"
    ],
    "polls": [
      {{
        "question": "Poll question",
        "option1": "Option A",
        "option2": "Option B"
      }}
    ],
    "quizzes": [
      "Quiz question idea"
    ]
  }},
  "hashtags": {{
    "primary": ["#main1", "#main2", "#main3"],
    "secondary": ["#secondary1", "#secondary2"],
    "niche": ["#niche1", "#niche2"]
  }},
  "content_calendar": {{
    "days": {content_days},
    "schedule": [
      {{
        "day": 1,
        "day_name": "Monday",
        "content_type": "educational|promotional|engagement",
        "title": "Post title",
        "caption": "Full caption",
        "hashtags": ["#hashtag1"],
        "platform": "instagram|facebook|linkedin",
        "best_time": "suggested posting time"
      }}
    ]
  }}
}}

PLATFORM: {platform}
CONTENT_DAYS: {content_days}

Generate {len(answers) * 2} social captions (mix of types).
Generate {content_days} days of content calendar.
Generate 5-10 reel scripts.
Generate 10-15 post ideas.

Make all content authentic, engaging, and aligned with the brand's voice.
"""
    
    # 6. Call OpenAI with JSON response format
    try:
        system_prompt = """You are an expert social media strategist and content creator.
You create engaging, authentic social media content that matches brand voice.
Always respond with valid JSON only, no markdown formatting or code blocks.
The JSON must match the exact structure requested."""

        completion = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=4000,
        )
        
        # Parse JSON response
        content = completion.choices[0].message.content.strip()
        social_content = json.loads(content)

        memory_result = None
        try:
            from user_sessions.services.brand_memory import record_content_generation_memory
            memory_result = record_content_generation_memory(session.id, social_content, user=request.user)
        except Exception:
            memory_result = None
        
        response_payload = {
            "brand_voice": social_content.get("brand_voice", {}),
            "social_captions": social_content.get("social_captions", []),
            "post_ideas": social_content.get("post_ideas", []),
            "reel_scripts": social_content.get("reel_scripts", []),
            "story_content": social_content.get("story_content", {}),
            "hashtags": social_content.get("hashtags", {}),
            "content_calendar": social_content.get("content_calendar", {}),
            "total_answers_used": answers.count(),
        }
        if memory_result and memory_result.get("recorded"):
            response_payload["memory"] = memory_result
        return Response(response_payload, status=status.HTTP_200_OK)
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from OpenAI: {e}")
        return Response(
            {"detail": "AI returned invalid response format"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except OpenAIError as e:
        logger.exception("OpenAI error in social content generation")
        return Response(
            {"detail": "AI service temporarily unavailable"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception("Unexpected error in social content generation")
        return Response(
            {"detail": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )






@swagger_auto_schema(
    method='patch',
    operation_description="Edit a user conversation message (ChatGPT-like: edits message, deletes subsequent messages, and generates only a follow-up question)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'content': openapi.Schema(type=openapi.TYPE_STRING, description="Updated message content"),
        },
        required=['content']
    ),
    responses={
        200: openapi.Response(
            description="Message updated, subsequent messages deleted, and follow-up question generated",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "edited_message": openapi.Schema(type=openapi.TYPE_OBJECT),
                    "follow_up_question": openapi.Schema(type=openapi.TYPE_STRING),
                    "deleted_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "documents_searched": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "context_used": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                }
            )
        ),
        403: "Cannot edit assistant messages or session locked",
        404: "Conversation not found",
        500: "AI service error"
    }
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, HasRolePermission])
def edit_conversation(request, pk, conversation_id):
    """
    ChatGPT-like behavior:
    1. Edit the user message
    2. Delete all subsequent messages in the thread
    3. Generate ONLY a follow-up question (assistant message) - no improved answer
    """
    session = get_object_or_404(Session, pk=pk)

    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    if not session.can_edit_answers(request.user):
        return Response({"detail": "Session is locked."}, status=403)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, session=session)
    
    # Only allow editing user messages
    if conversation.role != 'user':
        return Response({"detail": "Cannot edit assistant messages"}, status=403)
    
    content = request.data.get('content', '').strip()
    if not content:
        return Response({"detail": "Content is required"}, status=400)
    
    # Step 1: Update the edited message
    conversation.content = content
    conversation.save()
    
    # Step 2: Delete all subsequent messages (ChatGPT behavior)
    subsequent_conversations = Conversation.objects.filter(
        session=session,
        question=conversation.question,
        created_at__gt=conversation.created_at
    )
    deleted_count = subsequent_conversations.count()
    subsequent_conversations.delete()
    
    # Step 3: Generate ONLY a follow-up question using updated conversation history
    question = conversation.question
    draft = conversation.content.strip()
    question_text = question.text.strip()
    
    # Get conversation history up to (and including) the edited message
    history_qs = Conversation.objects.filter(
        session=session,
        question=question,
        created_at__lte=conversation.created_at
    ).order_by('created_at')
    
    history_messages = [
        {"role": "assistant" if c.role == "assistant" else "user", "content": c.content}
        for c in history_qs
    ]
    
    # RAG context (user-scoped documents + ai_knowledge)
    rag_sources = []
    rag_graph_concepts = []
    documents_searched = 0
    context = ""
    try:
        rag_bundle = build_combined_context_for_draft(
            question_text,
            draft,
            request.user,
            session=session,
            top_k=8,
            embedding_service=embedding_service,
            es_service=es_service,
        )
        context = rag_bundle["context"]
        rag_sources = rag_bundle["sources"]
        rag_graph_concepts = rag_bundle.get("graph_concepts") or []
        documents_searched = rag_bundle["documents_searched"]
    except Exception as e:
        logger.error("Context retrieval failed: %s", e)

    # Get foundation answer if exists
    foundation = ""
    try:
        foundation_obj = Answer.objects.get(session=session, question=question)
        foundation = foundation_obj.answer_text.strip()
    except Answer.DoesNotExist:
        pass
    
    # Get brand profile from other questions
    other_questions_answers = Answer.objects.filter(
        session=session
    ).exclude(question=question).select_related('question').order_by('question__stage', 'question__order')
    
    brand_profile_parts = []
    for ans in other_questions_answers:
        brand_profile_parts.append(f"Q: {ans.question.text}\nA: {ans.answer_text}")
    
    brand_profile_summary = "\n\n".join(brand_profile_parts) if brand_profile_parts else "No previous answers from other questions yet"
    
    # Build prompt - ONLY generate follow-up question (no improved_answer)
    task_block = """
    TASK — Follow-Up Question ONLY:

    Generate ONLY a follow-up question based on the user's edited answer.
    DO NOT generate an improved_answer - the user has already edited their answer.

    Inside "follow_up_question", you MUST structure your message as THREE paragraphs:

    PARAGRAPH 1 — ⭐ APPRECIATION
    • 1–2 short sentences
    • Recognize what they expressed in their edited answer
    • Strong, direct tone — one emoji max here if helpful

    <blank line required>

    PARAGRAPH 2 — 🧭 SUGGESTIONS
    • 2–4 short sentences
    • Give specific, actionable coaching based on their edited answer:
    - Behavior-based proof or example
    - Weak → Strong word upgrades (if needed)
    - How to make the emotional impact VIVID
    • Explain WHY the upgrade matters — unforgettable > nice

    <blank line required>

    PARAGRAPH 3 — ❓ ONE GUIDING QUESTION
    • ONE question, 10–15 words max
    • Push deeper into the transformation or real-life behavior
    • Simple human language

    TONE:
    • Bold, direct, supportive — strategist energy
    • Minimal emojis, only to reinforce belief 🙌
    • Push away from safe, generic answers every turn

    📌 REQUIRED OUTPUT — JSON ONLY:
    {
    "follow_up_question": "3-paragraph message"
    }
    """
    
    prompt = f"""
    🎩 ROLE:
    You are THE BRAND GODFATHER — world-class brand strategist.
    Your purpose: reveal the truth of the brand — not decorate it.

    🧠 CORE PRINCIPLES:
    • Brands must be FELT — emotion > explanation
    • Behavior proves words — no behavior = wrong word
    • Specific > vague, vivid > generic, bold > safe
    • You believe in them more than they believe in themselves 😎

    🚫 FORBIDDEN (never accept these without coaching):
    "quality", "professional", "innovative", "best service", "creative", "inspiring", "helpful", "reliable"
    → if any appear, suggest stronger, behavior-backed wording

    CONTEXT:
    Current question: {question_text}
    User's EDITED answer: {draft}
    Foundation (if any): {foundation or "None"}
    Brand Profile: {brand_profile_summary}
    History: {json.dumps(history_messages, ensure_ascii=False, indent=2) if history_messages else "None"}
    KB context: {context or "None"}

    🔥 NON-NEGOTIABLE:
    • Push into truth every turn
    • Celebrate courage — but don't let them hide
    • Add Minimal emojis which will be visible at least — used like seasoning, not like confetti
    • Never speak in corporate tone
    • You are building a world-famous brand with them — act like it

    {task_block}
    """
    
    # Generate new AI response
    try:
        david_system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.

CORE RULES:
1. Base ALL responses on the provided document excerpts (David's teachings)
2. Speak in bold, direct, no-jargon tone
3. Use stories and examples from the excerpts when available
4. Never give generic marketing advice — every response must reflect David's philosophy
5. If document context is provided, you MUST use it

DAVID'S PHILOSOPHY:
• A brand is a promise KEPT, not made
• Brands must be FELT — emotion beats explanation
• Behavior proves words — no behavior = wrong word
• Specific > vague, vivid > generic, bold > safe

Respond only with perfect JSON."""
        
        completion = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {"role": "system", "content": david_system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200,
        )
        
        result = json.loads(completion.choices[0].message.content.strip())
        follow_up = result.get("follow_up_question", "Can you tell me more?").strip()
        
        # Save ONLY the assistant follow-up question (no improved_answer)
        Conversation.objects.create(session=session, question=question, role="assistant", content=follow_up.strip())
        
        return Response({
            "edited_message": {
                "id": conversation.id,
                "content": conversation.content,
                "role": conversation.role,
                "created_at": conversation.created_at,
            },
            "follow_up_question": follow_up,
            "deleted_count": deleted_count,
            "documents_searched": documents_searched,
            "context_used": bool(context),
            "sources": rag_sources,
            "graph_concepts": rag_graph_concepts,
        }, status=200)
        
    except json.JSONDecodeError:
        logger.error("AI returned invalid JSON")
        return Response({"detail": "AI response was malformed"}, status=500)
    except OpenAIError as e:
        logger.exception("OpenAI error")
        return Response({"detail": "AI service temporarily unavailable"}, status=500)
    except Exception as e:
        logger.exception("Unexpected error in AI regeneration")
        return Response({"detail": "Internal server error"}, status=500)





@swagger_auto_schema(
    method='POST',
    operation_description="Generate Foundation summary (structured: heading, sub_heading, sections for UI)",
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "summary": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sub_heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sections": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                                        "content": openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                )
                            ),
                        }
                    ),
                    "total_questions_answered": openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        ),
        400: "No answers found",
        403: "Access denied",
        404: "Session not found",
        500: "AI service error",
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_generate_foundation_summary(request, pk):
    """
    POST /api/sessions/<pk>/generate-foundation-summary/
    Generates and saves Foundation summary.
    """

    # 1. Session access check
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    # 2. Get ONLY Foundation stage answers
    answers = Answer.objects.filter(
        session=session,
        question__stage=1,
        question__is_active=True
    ).select_related('question').order_by('question__order')

    if not answers.exists():
        return Response(
            {"detail": "No Foundation answers found. Please complete Foundation questions first."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Build Q&A text
    qa_text = ""
    qa_pairs = []

    for answer in answers:
        question_text = answer.question.text.strip()
        answer_text = answer.answer_text.strip()

        qa_text += f"Q: {question_text}\n"
        qa_text += f"A: {answer_text}\n\n"

        qa_pairs.append({
            'question': question_text,
            'answer': answer_text
        })

    # 4. Create / update DB row → processing
    summary_obj, _ = FoundationSummary.objects.get_or_create(
        session=session,
        defaults={
            "status": "processing",
            "generated_by": request.user
        }
    )
    summary_obj.status = "processing"
    summary_obj.error_message = None
    summary_obj.save()

    use_async = request.data.get("async", settings.AI_HEAVY_ENDPOINTS_ASYNC)
    if use_async:
        try:
            from user_sessions.tasks import generate_foundation_summary_task
            task = generate_foundation_summary_task.delay(session.pk, request.user.pk)
            return Response({
                "message": "Foundation summary generation started",
                "task_id": task.id,
                "status": "processing",
                "poll_url": f"/api/sessions/ai-tasks/{task.id}/",
            })
        except Exception as e:
            logger.warning("Celery foundation summary enqueue failed, running sync: %s", e)

    from user_sessions.services.ai_generation_service import run_foundation_summary_generation
    gen_result = run_foundation_summary_generation(session.pk, request.user.pk)
    if gen_result.get("success"):
        summary_payload = gen_result["summary"] if isinstance(gen_result.get("summary"), dict) else _parse_structured_summary(gen_result.get("summary") or "")
        brand_book = _build_brand_book_payload(session, summary_payload)
        return Response({
            "summary": summary_payload,
            "brand_book": brand_book,
            "total_questions_answered": len(qa_pairs),
            "sources": gen_result.get("sources", []),
            "brand_book_reference_sources": gen_result.get("brand_book_reference_sources", []),
        }, status=status.HTTP_200_OK)

    summary_obj.refresh_from_db()
    return Response(
        {"detail": gen_result.get("error", "Generation failed")},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@swagger_auto_schema(
    method='get',
    operation_description="Get Foundation summary (structured: heading, sub_heading, sections when available)",
    responses={
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "summary": openapi.Schema(
                        description="Structured { heading, sub_heading, sections } or legacy string",
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sub_heading": openapi.Schema(type=openapi.TYPE_STRING),
                            "sections": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        }
                    ),
                    "status": openapi.Schema(type=openapi.TYPE_STRING),
                    "generated_by": openapi.Schema(type=openapi.TYPE_STRING),
                    "updated_at": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        403: "Access denied",
        404: "Summary not found",
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_get_foundation_summary(request, pk):
    """
    GET /api/sessions/<pk>/foundation-summary/
    Returns saved Foundation summary.
    """

    # 1. Session access check
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    # 2. Get summary
    try:
        summary_obj = FoundationSummary.objects.get(session=session)
    except FoundationSummary.DoesNotExist:
        return Response(
            {"detail": "Foundation summary not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Return summary in same structure as generate: parse if JSON, else legacy string
    summary_value = summary_obj.summary_text
    if summary_value and summary_value.strip().startswith("{"):
        try:
            summary_value = json.loads(summary_value)
        except (json.JSONDecodeError, TypeError):
            pass
    elif summary_value:
        summary_value = _parse_structured_summary(summary_value)

    brand_book = _build_brand_book_payload(session, summary_value if isinstance(summary_value, dict) else _parse_structured_summary(summary_value))

    return Response({
        "summary": summary_value,
        "brand_book": brand_book,
        "status": summary_obj.status,
        "generated_by": summary_obj.generated_by.email if summary_obj.generated_by else None,
        "updated_at": summary_obj.updated_at,
    }, status=status.HTTP_200_OK)




@swagger_auto_schema(
    method='put',
    operation_description="Edit Foundation summary",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "summary": openapi.Schema(type=openapi.TYPE_STRING, description="Updated summary text"),
        },
        required=["summary"]
    ),
    responses={
        200: "Updated successfully",
        400: "Invalid input",
        403: "Access denied",
        404: "Summary not found",
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, HasRolePermission])
def session_update_foundation_summary(request, pk):
    """
    PUT /api/sessions/<pk>/update-foundation-summary/
    Edit existing Foundation summary.
    """

    # 1. Session access check
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    # 2. Get existing summary
    try:
        summary_obj = FoundationSummary.objects.get(session=session)
    except FoundationSummary.DoesNotExist:
        return Response(
            {"detail": "Foundation summary not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # 3. Validate input (accept string or structured { heading, sub_heading, sections })
    new_summary = request.data.get("summary")
    if new_summary is None:
        return Response(
            {"detail": "Summary is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if isinstance(new_summary, dict):
        summary_to_store = json.dumps(new_summary)
        summary_to_return = new_summary
    else:
        s = (new_summary or "").strip()
        if not s:
            return Response(
                {"detail": "Summary text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        summary_to_store = s
        summary_to_return = _parse_structured_summary(s)

    prior_text = (summary_obj.summary_text or "").strip()

    # 4. Update DB
    summary_obj.summary_text = summary_to_store
    summary_obj.status = "completed"
    summary_obj.error_message = None
    summary_obj.generated_by = request.user
    summary_obj.save()

    feedback_result = None
    new_text = summary_to_store if isinstance(summary_to_store, str) else json.dumps(summary_to_store)
    if prior_text and new_text.strip() and prior_text != new_text.strip():
        try:
            from user_sessions.services.feedback_learning import learn_from_human_edit
            feedback_result = learn_from_human_edit(
                session.id,
                prior_text,
                new_text.strip(),
                user=request.user,
                source="foundation_summary_edit",
            )
        except Exception:
            feedback_result = None

    resp = {
        "message": "Foundation summary updated successfully",
        "summary": summary_to_return,
        "brand_book": _build_brand_book_payload(session, summary_to_return if isinstance(summary_to_return, dict) else _parse_structured_summary(summary_to_return)),
    }
    if feedback_result and feedback_result.get("learned"):
        resp["feedback_learning"] = {"learned": True}
    return Response(resp, status=status.HTTP_200_OK)





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def answer_ai_suggestions(request, pk):
    """
    Called while user is typing.
    Classifies the answer internally, then returns warm coaching recommendations.
    """
    from user_sessions.services.answer_quality import (
        build_quality_prompt_context,
        normalize_ai_quality_response,
        score_answer_quality,
    )

    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=403)

    question_id = request.data.get("question_id")
    hints = (request.data.get("hints") or "").strip()
    intent = (request.data.get("intent") or "refine").strip().lower()
    custom_question = (request.data.get("custom_question") or "").strip()[:600]
    allowed_intents = {"refine", "example", "context", "why", "hint", "explain", "ask"}
    if intent not in allowed_intents:
        intent = "refine"

    try:
        question = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return Response({"detail": "Question not found"}, status=404)

    heuristic = score_answer_quality(question, hints)
    question_stage = int(getattr(question, "stage", 1) or 1)
    include_suggestion_quote = question_stage >= 2
    active_pipeline = get_active_pipeline_name()
    rag_phase = None
    rag_context = ""
    rag_sources = []

    try:
        retrieval = retrieve_context(
            (
                "AI answer suggestion for Brand Godfather discovery question. "
                f"Question: {question.text.strip()} Answer: {hints}"
            ),
            user=request.user,
            session=session,
            session_id=session.id,
            include_knowledge=True,
            agent_id="strategist",
            top_k=5,
            max_chars=2500,
        )
        active_pipeline = retrieval.get("active_pipeline") or active_pipeline
        rag_phase = retrieval.get("rag_phase")
        rag_context = str(retrieval.get("context") or "").strip()
        rag_sources = retrieval.get("sources") or []
    except Exception as e:
        logger.warning("AI answer suggestions RAG context failed session=%s question=%s: %s", pk, question_id, e)

    if active_pipeline == "rag_v2" and not rag_context:
        rag_context = (
            f"RAGv2 is the active Brand Godfather pipeline for phase {question_stage}. "
            "Use the phase prompt, question stage, and session answers as the strategic source of truth."
        )
    if active_pipeline and not rag_sources:
        rag_sources = [{
            "title": "Active Brand Godfather pipeline",
            "source": active_pipeline,
            "type": "pipeline",
            "excerpt": f"{active_pipeline} selected by admin AI tuning for phase {question_stage} answer guidance.",
        }]

    if intent != "refine":
        intent_labels = {
            "example": "Give one strong example answer the user can learn from, but do not force them to copy it.",
            "context": "Give additional strategic context behind the question.",
            "why": "Explain why this question matters to the Brand Book and brand strategy.",
            "hint": "Give a concise hint that helps the user answer in their own words.",
            "explain": "Explain what the question is really asking in simple language.",
            "ask": "Answer the user's custom question as the Brand Godfather.",
        }
        system_prompt = """You are THE BRAND GODFATHER — a strategic brand guide inside a question flow.

The user is not asking for a rewrite unless explicitly requested. Help them understand, think, and answer better.
Be concise, specific, emotionally intelligent, and grounded in the active RAG/context.
Do not use generic AI helper language. Do not over-explain.

Return JSON only:
{
  "mode": "example|context|why|hint|explain|ask",
  "title": "short label",
  "answer": "helpful response, 2-5 sentences max",
  "example_answer": "optional example answer only when useful"
}
"""
        user_prompt = f"""Active BGF pipeline: {active_pipeline}
RAG phase: {rag_phase or "auto"}
Phase number: {question_stage}
Mode requested: {intent}
Mode instruction: {intent_labels.get(intent)}

Question being answered:
{question.text.strip()}

User answer, if any:
{hints or "No answer yet."}

User's custom question, if any:
{custom_question or "None"}

Retrieved brand/RAG context from the active pipeline:
{rag_context[:2500] if rag_context else "No retrieved context available."}
"""
        try:
            completion = get_openai_client().chat.completions.create(
                model=get_openai_chat_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.55,
                max_tokens=420,
            )
            text = completion.choices[0].message.content.strip()
            result = json.loads(text)
            return Response({
                "mode": intent,
                "title": result.get("title") or intent.replace("_", " ").title(),
                "answer": result.get("answer") or "Think about the most honest strategic truth behind this question.",
                "example_answer": result.get("example_answer") or "",
                "active_pipeline": active_pipeline,
                "pipeline_source": "admin_ai_tuning",
                "rag_phase": rag_phase,
                "phase_number": question_stage,
                "rag_context_used": bool(rag_context),
                "sources": rag_sources[:5],
            }, status=200)
        except Exception as e:
            logger.warning("AI question helper failed session=%s question=%s intent=%s: %s", pk, question_id, intent, e)
            fallback_answers = {
                "example": "A strong answer usually names a belief, shows why it matters, and makes it feel specific to your brand.",
                "context": "This question is looking for the strategic truth underneath your answer, not a polished marketing line.",
                "why": "This matters because your answer becomes part of the emotional and strategic foundation of the Brand Book.",
                "hint": "Start with: 'We believe...' then finish with something only your brand would truly stand behind.",
                "explain": "In simple terms, this question is asking what you really believe and why anyone should feel it.",
                "ask": "Use the question, your answer, and the brand truth you already know as the source of the answer.",
            }
            return Response({
                "mode": intent,
                "title": intent.replace("_", " ").title(),
                "answer": fallback_answers.get(intent, fallback_answers["hint"]),
                "example_answer": "",
                "active_pipeline": active_pipeline,
                "pipeline_source": "admin_ai_tuning",
                "rag_phase": rag_phase,
                "phase_number": question_stage,
                "rag_context_used": bool(rag_context),
                "sources": rag_sources[:5],
            }, status=200)

    system_prompt = """You are THE BRAND GODFATHER — a world-class brand strategist coach.

You evaluate a user's partial or full answer against the specific question they are answering.

Your job:
1) Classify the answer into exactly ONE internal quality tier:
    - too_weak → quality_label must be an empty string
    - vendor_thought → quality_label must be an empty string
    - strong → quality_label must be an empty string

2) Give a one-sentence reason that feels like a supportive strategist, not a harsh judge.
    Never say "weak", "too weak", "bad", "lacks", or "vendor pitch" in user-facing copy.
    Never use the word "draft" in user-facing copy; say "your answer" when needed.
    Do not use old quality-heading phrases; keep the reason conversational and respectful.
    Write in English only.

3) Give 2–3 strings in "suggestions" — each MUST be only the final answer text the user pastes in (one sentence).
   Never wrap with "Rewrite with...", "Try this instead:", or "like '...'".
    Every suggestion must be strong enough for the Brand Godfather ORB gate: it answers this exact question, names a belief or deeper purpose, includes a specific human change or behavior, and avoids product/service/vendor language.

4) If phase_number is 2 or higher, include "suggestion_quote": a short original strategic quote, grounded in the retrieved context and the user's answer, that can sit above the suggestions. If phase_number is 1, return an empty string.

Rules:
- Vendor trap = "we provide solutions", "unmet market needs", generic services talk, sounding hireable not memorable.
- Weak = too short, generic buzzwords, no felt truth, no proof of behavior.
- Strong = specific, ownable, emotional or behavioral truth that fits the question.
- Use the question profile and heuristic hint; override only if clearly wrong.
- For "beyond what you sell" or purpose questions, the suggestion must name the deeper human change the brand exists to create and why that matters.
- Reject poetic but unclear copy inside your own reasoning; do not output it as a recommendation.

Output JSON only:
{
  "quality": "too_weak|vendor_thought|strong",
    "quality_label": "",
  "reason": "...",
    "suggestion_quote": "...",
  "suggestions": ["...", "..."]
}"""

    user_prompt = f"""Active BGF pipeline: {active_pipeline}
RAG phase: {rag_phase or "auto"}
Phase number: {question_stage}
Include suggestion quote: {"yes" if include_suggestion_quote else "no"}

Question: {question.text.strip()}

User answer: {hints}

Retrieved brand/RAG context from the active pipeline:
{rag_context[:2500] if rag_context else "No retrieved context available."}

{build_quality_prompt_context(question, hints, heuristic)}"""

    try:
        completion = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.65,
            max_tokens=450,
        )

        text = completion.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        payload = normalize_ai_quality_response(result, heuristic)
        quote_text = str(result.get("suggestion_quote") or "").strip() if include_suggestion_quote else ""
        payload["active_pipeline"] = active_pipeline
        payload["pipeline_source"] = "admin_ai_tuning"
        payload["rag_phase"] = rag_phase
        payload["phase_number"] = question_stage
        payload["rag_context_used"] = bool(rag_context)
        payload["suggestion_quote"] = {
            "enabled": bool(quote_text),
            "quote": quote_text,
            "source": "rag_v2_phase_prompt" if active_pipeline == "rag_v2" else "active_pipeline",
            "active_pipeline": active_pipeline,
            "rag_phase": rag_phase,
            "rag_context_used": bool(rag_context),
            "sources": rag_sources[:3],
        }
        payload["sources"] = rag_sources[:5]
        return Response(payload, status=200)

    except (json.JSONDecodeError, KeyError):
        payload = normalize_ai_quality_response(
            {"suggestions": _fallback_suggestions(heuristic)},
            heuristic,
        )
        payload["active_pipeline"] = active_pipeline
        payload["pipeline_source"] = "admin_ai_tuning"
        payload["rag_phase"] = rag_phase
        payload["phase_number"] = question_stage
        payload["rag_context_used"] = bool(rag_context)
        payload["suggestion_quote"] = {
            "enabled": False,
            "quote": "",
            "source": "fallback",
            "active_pipeline": active_pipeline,
            "rag_phase": rag_phase,
            "rag_context_used": bool(rag_context),
            "sources": rag_sources[:3],
        }
        payload["sources"] = rag_sources[:5]
        return Response(payload, status=200)
    except Exception:
        return Response({"detail": "AI service error"}, status=500)


def _fallback_suggestions(heuristic: dict) -> list:
    """Rule-based suggestions when AI JSON parsing fails."""
    q = heuristic.get("quality", "too_weak")
    profile = heuristic.get("profile") or {}
    step = str(profile.get("step") or "").lower()

    if "culture" in step or "purpose" in step:
        return [
            "We exist to help people feel the shift from being managed by the market to moving with their own conviction, because that is where lasting trust begins.",
            "Beyond what we sell, our purpose is to make people feel seen, steadier, and brave enough to choose a different standard for themselves.",
        ]

    if q == "vendor_thought":
        return [
            "We believe people remember the brands that change how they feel and act, so every decision we make must create trust before it creates a transaction.",
            "Our brand stands for refusing the easy, forgettable answer and building the kind of clarity people can feel in the room.",
        ]
    if q == "strong":
        return [
            "We carry this belief into the way we show up: direct enough to create clarity, warm enough to earn trust, and disciplined enough to repeat it every time.",
        ]
    return [
        "We believe our work should leave people feeling clearer, braver, and less willing to accept the ordinary version of what they came for.",
        "The deeper reason we exist is to turn uncertainty into conviction, so people can move forward with a standard they actually believe in.",
    ]


# ---- Contextual assistant suggestion (avatar popup) ----
ASSISTANT_SUGGESTION_SYSTEM_PROMPT = """You are a supportive, concise onboarding assistant for a brand-building product. You will receive the user's current page (route), how long they have been on the page (time_on_page_seconds), their progress (current_step_index, total_steps, answers_count), and last_action (e.g. answered, focused, scrolled, idle).

Your task: Return exactly one short, encouraging message (1–2 sentences) that feels personal and inspiring. Tone: warm, motivating, no pressure. Do not repeat the same phrase every time; vary the message based on progress, route, and last_action.

Important: Do NOT say "click here" or "click there" or point to specific buttons. Speak about the overall screen and context — what this page is for, how they're doing on this screen, what they can do in general here. The message should describe the screen and their progress, not instruct them to click something. Examples of good phrasing: "You're on the foundation questions — halfway through already.", "This is your manifesto screen; everything here is yours to review or edit.", "Your dashboard is where you pick your next step."

Route-specific behavior (always about the screen as a whole, not "click here"):
- foundation-questions: Acknowledge this screen (foundation questions), progress (e.g. "You're halfway through these questions."), or that the next question is waiting — no "click" wording.
- ChatKickoffPage: Acknowledge this chat/kickoff screen and how many they've answered.
- brand-summary, manifesto, manifestoFirstPage: Acknowledge what this screen shows (brand summary, manifesto) and that they can review or edit — screen-level, not button-level.
- user-dashboard: Acknowledge the dashboard and that they can start or continue a step from here.
- chat-unlock: Acknowledge the unlock screen if relevant.

CTA usage: Use "review_journey" when the message is about reviewing progress or the journey (so the frontend can show the journey/review screen or section). Use "quick_tips" when the message is about tips or guidance (so the frontend can show the tips screen or panel). Use null for general encouragement. CTA tells the frontend which overall screen/section is relevant; the message describes that context, not a specific click.

Output format: Return only valid JSON, no markdown or extra text. Keys: "message" (string), "cta" (string or null). Allowed cta values: null, "review_journey", "quick_tips". Example: {"message": "You're on the foundation questions — great progress so far.", "cta": null}"""


@swagger_auto_schema(
    method='post',
    operation_description="Get a short contextual suggestion for the avatar bubble based on route and progress.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['route'],
        properties={
            'route': openapi.Schema(type=openapi.TYPE_STRING, description='e.g. /foundation-questions, /ChatKickoffPage'),
            'time_on_page_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
            'current_step_index': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
            'total_steps': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
            'answers_count': openapi.Schema(type=openapi.TYPE_INTEGER),
            'last_action': openapi.Schema(type=openapi.TYPE_STRING, enum=['answered', 'focused', 'scrolled', 'idle']),
        },
    ),
    responses={200: openapi.Response('message, cta', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING), 'cta': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)})), 403: "Access denied", 500: "AI error"},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assistant_suggestion(request, pk):
    """
    POST /api/sessions/{session_id}/assistant-suggestion/
    Returns one short encouraging message and optional cta for the avatar bubble.
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    route = (request.data.get("route") or "").strip()
    if not route:
        return Response({"detail": "route is required"}, status=status.HTTP_400_BAD_REQUEST)

    time_on_page_seconds = request.data.get("time_on_page_seconds")
    if time_on_page_seconds is None:
        time_on_page_seconds = 0
    try:
        time_on_page_seconds = int(float(time_on_page_seconds))
    except (TypeError, ValueError):
        time_on_page_seconds = 0

    current_step_index = request.data.get("current_step_index")
    total_steps = request.data.get("total_steps")
    answers_count = request.data.get("answers_count")
    last_action = (request.data.get("last_action") or "idle").strip().lower()
    if last_action not in ("answered", "focused", "scrolled", "idle"):
        last_action = "idle"

    user_prompt = f"route={route}, time_on_page_seconds={time_on_page_seconds}, current_step_index={current_step_index}, total_steps={total_steps}, answers_count={answers_count}, last_action={last_action}"

    try:
        completion = get_openai_client().chat.completions.create(
            model=get_openai_chat_model(),
            messages=[
                {"role": "system", "content": ASSISTANT_SUGGESTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=200,
        )
        text = completion.choices[0].message.content.strip()
        # Strip markdown code fence if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        message = (result.get("message") or "").strip() or "Keep going — you're doing great!"
        cta = result.get("cta")
        if cta not in (None, "review_journey", "quick_tips"):
            cta = None
        return Response({"message": message, "cta": cta}, status=status.HTTP_200_OK)
    except json.JSONDecodeError:
        return Response({"message": "Keep going — you're doing great!", "cta": None}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"detail": "AI service error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasRolePermission])
def brand_book_heading_insight(request, pk):
    """
    POST /api/sessions/<pk>/brand-book-insight/
    Returns a short orb message for a hovered heading.
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    heading = (request.data.get("heading") or "").strip()
    content = (request.data.get("content") or "").strip()
    page_id = (request.data.get("page_id") or "").strip().lower()

    if not heading:
        return Response({"detail": "heading is required"}, status=status.HTTP_400_BAD_REQUEST)

    def first_sentence(text):
        t = (text or "").strip()
        if not t:
            return ""
        parts = [p.strip() for p in t.replace("\n", " ").split(".") if p.strip()]
        if not parts:
            return t
        s = parts[0]
        if not s.endswith("."):
            s += "."
        return s

    hl = heading.lower()
    if "overview" in hl:
        message = "This section gives you a high-level brand blueprint: identity, category position, and core purpose."
    elif "dna" in hl:
        message = "This section reveals your brand's core traits that shape tone, behavior, and decisions."
    elif "promise" in hl:
        message = "This heading clarifies the consistent outcome and experience customers should expect from your brand."
    elif "emotional" in hl:
        message = "This section highlights the before/after emotional shift and shows the core customer transformation."
    elif "differentiation" in hl:
        message = "This point explains your unique market edge and why your brand stands apart."
    elif "style" in hl or "tone" in hl or "visual" in hl:
        message = "This section decodes brand expression: voice, visual mood, and design direction in one place."
    elif "tagline" in hl:
        message = "This section gives concise messaging options that make your brand memorable."
    else:
        message = "This heading explains a focused strategic angle that can guide execution decisions."

    key_line = first_sentence(content)
    if key_line:
        message = f"{message} Key insight: {key_line}"

    return Response(
        {
            "heading": heading,
            "page_id": page_id or None,
            "message": message,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def session_brand_brain(request, pk):
    """GET/PATCH /api/sessions/<pk>/brand-brain/ — persistent brand operating state."""
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.brand_brain import get_brand_brain, save_brand_brain

    if request.method == 'GET':
        return Response({"brand_brain": get_brand_brain(session.id)})

    updates = request.data.get("brand_brain") or request.data
    if not isinstance(updates, dict):
        return Response({"detail": "brand_brain object required"}, status=status.HTTP_400_BAD_REQUEST)
    merged = save_brand_brain(session.id, {**get_brand_brain(session.id), **updates}, user=request.user)
    return Response({"brand_brain": merged})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def session_feedback_learning(request, pk):
    """
    GET  /api/sessions/<pk>/feedback-learning/ — learned preferences profile
    POST — Body: original_ai_text, edited_text (human feedback loop)
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.feedback_learning import (
        get_feedback_learning_profile,
        learn_from_human_edit,
    )

    if request.method == 'GET':
        return Response({"feedback_profile": get_feedback_learning_profile(session.id)})

    original = (request.data.get("original_ai_text") or request.data.get("original") or "").strip()
    edited = (request.data.get("edited_text") or request.data.get("edited") or "").strip()
    if not edited:
        return Response({"detail": "edited_text is required"}, status=status.HTTP_400_BAD_REQUEST)

    result = learn_from_human_edit(
        session.id,
        original,
        edited,
        context=(request.data.get("context") or ""),
        user=request.user,
        source=request.data.get("source") or "api",
    )
    try:
        from user_sessions.services.product_signals import record_product_signal

        record_product_signal(session.id, "feedback_edit", {"learned": result.get("learned")})
    except Exception:
        pass
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def brand_workflows_catalog(request):
    """GET /api/sessions/brand-workflows/ — product workflow catalog."""
    from user_sessions.services.brand_workflows import list_product_workflows

    return Response({
        "architecture_frozen": True,
        "workflows": list_product_workflows(),
        "pack": "POST .../brand-workflow/ with workflow=pack or full",
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def session_brand_workflow(request, pk):
    """
    POST /api/sessions/<pk>/brand-workflow/
    Body: workflow (brand_dna|messaging_framework|positioning_engine|pack|full), extra_context
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    workflow = (request.data.get("workflow") or "brand_dna").strip().lower()
    from user_sessions.services.brand_workflows import (
        run_brand_workflow,
        run_product_pack,
    )

    if workflow in ("full", "pack"):
        result = run_product_pack(session_id=session.id, user=request.user, session=session)
    else:
        result = run_brand_workflow(
            workflow,
            session_id=session.id,
            user=request.user,
            session=session,
            extra_context=request.data.get("extra_context") or "",
            agent_id=request.data.get("agent_id") or "branding",
        )
    if result.get("error"):
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    try:
        from user_sessions.services.product_signals import record_product_signal

        sig = "workflow_run"
        events = []
        try:
            from user_sessions.models import BrandMemory

            row = BrandMemory.objects.filter(session_id=session.id, key="product_signals").first()
            events = [e.get("meta", {}).get("workflow") for e in (row.value or {}).get("events", [])]
        except Exception:
            pass
        if workflow in events[-5:]:
            sig = "workflow_rerun"
        record_product_signal(session.id, sig, {"workflow": workflow})
    except Exception:
        pass
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_longitudinal_memory(request, pk):
    """GET /api/sessions/<pk>/longitudinal-memory/ — pinned strategic positions."""
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.longitudinal_memory import get_longitudinal_positions
    from user_sessions.services.brand_brain import get_brand_brain

    brain = get_brand_brain(session.id)
    return Response({
        "positions": get_longitudinal_positions(session.id),
        "evolution_history": brain.get("evolution_history") or [],
        "brand_brain": brain,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def product_observability_dashboard(request):
    """GET /api/sessions/product-observability/ — enterprise cognition KPIs."""
    from user_sessions.services.product_observability import get_product_observability_dashboard

    return Response(get_product_observability_dashboard())


def _run_brand_export_package(session, workflow, user):
    from user_sessions.services.brand_workflows import run_brand_workflow, run_product_pack

    narrative = ""
    if workflow in ("pack", "full"):
        result = run_product_pack(session_id=session.id, user=user, session=session)
        package = result.get("brand_operating_system") or {}
    else:
        result = run_brand_workflow(
            workflow,
            session_id=session.id,
            user=user,
            session=session,
        )
        package = result.get("structured") or {}
        narrative = result.get("narrative") or ""
    return result, package, narrative


def _summary_export_text_from_payload(brand_book, summary):
    lines = []
    if isinstance(summary, dict):
        if summary.get("heading"):
            lines.append(str(summary.get("heading")))
        if summary.get("sub_heading"):
            lines.append(str(summary.get("sub_heading")))
        for section in summary.get("sections") or []:
            if isinstance(section, dict):
                title = str(section.get("title") or "").strip()
                content = str(section.get("content") or "").strip()
                if title or content:
                    lines.append("\n".join(part for part in [title, content] if part))

    if isinstance(brand_book, dict):
        for page in brand_book.get("pages") or []:
            if not isinstance(page, dict):
                continue
            page_lines = []
            title = str(page.get("title") or "").strip()
            if title:
                page_lines.append(title)
            for field in page.get("overview_fields") or []:
                if isinstance(field, dict):
                    label = str(field.get("label") or "").strip()
                    value = str(field.get("value") or "").strip()
                    if label or value:
                        page_lines.append(f"{label}: {value}" if label else value)
            dna_points = page.get("dna_points") or []
            if dna_points:
                dna_lines = []
                for point in _normalize_brand_dna_points(dna_points):
                    dna_lines.append(" - ".join(part for part in [point.get("title"), point.get("content")] if part))
                page_lines.append("Brand DNA: " + "; ".join(dna_lines))
            for section in page.get("sections") or []:
                if isinstance(section, dict):
                    section_title = str(section.get("title") or "").strip()
                    content = str(section.get("content") or "").strip()
                    if section_title or content:
                        page_lines.append("\n".join(part for part in [section_title, content] if part))
            emotional = page.get("emotional_connection") or {}
            if isinstance(emotional, dict):
                emotional_parts = [
                    emotional.get("title"),
                    emotional.get("before_title"),
                    emotional.get("before"),
                    emotional.get("after_title"),
                    emotional.get("after"),
                ]
                emotional_text = "\n".join(str(part).strip() for part in emotional_parts if part)
                if emotional_text:
                    page_lines.append(emotional_text)
            if page.get("statement"):
                page_lines.append(str(page.get("statement")))
            style_tone = page.get("style_tone") or {}
            if isinstance(style_tone, dict):
                style_parts = [
                    style_tone.get("title"),
                    style_tone.get("summary"),
                    style_tone.get("tone"),
                    style_tone.get("visual"),
                    style_tone.get("design"),
                ]
                style_text = "\n".join(str(part).strip() for part in style_parts if part)
                if style_text:
                    page_lines.append(style_text)
            taglines = page.get("taglines") or []
            if taglines:
                page_lines.append("Taglines: " + " | ".join(str(tagline) for tagline in taglines if tagline))
            if page_lines:
                lines.append("\n".join(page_lines))
    return "\n\n".join(line for line in lines if str(line).strip())


def _build_summary_export_package(session, data):
    brand_book = data.get("brand_book") if isinstance(data, dict) else {}
    summary = data.get("summary") if isinstance(data, dict) else {}

    if not brand_book and not summary:
        try:
            summary_obj = FoundationSummary.objects.filter(session=session, status="completed").first()
            summary_text = summary_obj.summary_text if summary_obj else ""
            if summary_text and summary_text.strip().startswith("{"):
                summary = json.loads(summary_text)
            elif summary_text:
                summary = _parse_structured_summary(summary_text)
            else:
                summary = {}
            brand_book = _build_brand_book_payload(session, summary if isinstance(summary, dict) else {})
        except Exception:
            summary = {}
            brand_book = {}

    narrative = _summary_export_text_from_payload(brand_book or {}, summary or {})
    brand_name = ""
    if isinstance(brand_book, dict):
        brand_name = str(brand_book.get("brand_name") or "").strip()
    if not brand_name:
        brand_name = session.title or "Brand"

    heading = summary.get("heading") if isinstance(summary, dict) else ""
    sub_heading = summary.get("sub_heading") if isinstance(summary, dict) else ""
    package = {
        "brand_dna": {
            "narrative": narrative or sub_heading or heading or f"Brand summary for {brand_name}.",
            "core_beliefs": [],
            "non_negotiables": [],
            "emotional_promise": sub_heading or "",
            "differentiation_anchor": heading or "",
        },
        "positioning": {
            "category": heading or "Brand Overview",
            "competitive_frame": sub_heading or narrative[:500],
        },
    }
    return package, narrative, brand_name


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def session_brand_export(request, pk):
    """
    POST/GET /api/sessions/<pk>/brand-export/
    Query/body: workflow, export_format (json|pdf|pptx)
    """
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data if request.method == "POST" else {}
    workflow = (
        data.get("workflow")
        or request.query_params.get("workflow")
        or "pack"
    ).strip().lower()
    fmt = (
        data.get("export_format")
        or data.get("format")
        or request.query_params.get("export_format")
        or request.query_params.get("file_format")
        or request.query_params.get("format")
        or "json"
    ).strip().lower()

    if workflow in ("brand_summary", "brand_book", "summary"):
        package, narrative, client_name = _build_summary_export_package(session, data)
        result = {"brand_operating_system": package, "explainability": {}}
        title = f"{client_name or session.title or 'Brand'} — Brand Book"
    else:
        result, package, narrative = _run_brand_export_package(session, workflow, request.user)
        title = f"{session.title or 'Brand'} — {workflow.replace('_', ' ').title()}"

    from user_sessions.services.brand_export_engine import (
        record_export_audit,
        render_brand_pptx,
        workflow_display_name,
    )

    styled = (
        str(data.get("styled") or request.query_params.get("styled") or "").lower()
        in ("1", "true", "yes", "premium")
    )
    client_name = (client_name if workflow in ("brand_summary", "brand_book", "summary") else session.title) or f"Session {session.id}"

    if fmt == "pdf":
        if styled:
            from user_sessions.services.brand_export_premium import render_premium_brand_pdf

            pdf_bytes = render_premium_brand_pdf(
                workflow_display_name(workflow),
                package,
                narrative=narrative,
                client_name=client_name,
            )
        else:
            from user_sessions.services.brand_export_engine import render_brand_pdf

            pdf_bytes = render_brand_pdf(
                workflow_display_name(workflow),
                package,
                narrative=narrative,
            )
        record_export_audit(session.id, workflow, "pdf", request.user)
        from django.http import HttpResponse

        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="brand-{workflow}-{session.id}.pdf"'
        return resp

    if fmt in ("pptx", "ppt"):
        try:
            ppt_bytes = render_brand_pptx(workflow_display_name(workflow), package, narrative=narrative)
        except ImportError:
            return Response(
                {"detail": "PPT export requires python-pptx on server"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        record_export_audit(session.id, workflow, "pptx", request.user)
        from django.http import HttpResponse

        resp = HttpResponse(
            ppt_bytes,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        resp["Content-Disposition"] = f'attachment; filename="brand-{workflow}-{session.id}.pptx"'
        return resp

    export_doc = {
        "title": title,
        "session_id": session.id,
        "workflow": workflow,
        "brand_operating_system": package,
        "narrative": narrative[:8000] if narrative else "",
        "explainability": result.get("explainability")
        or next(iter((result.get("workflow_results") or {}).values()), {}).get("explainability", {}),
        "generated_at": timezone.now().isoformat(),
    }
    record_export_audit(session.id, workflow, "json", request.user)
    return Response({"export": export_doc, "formats_available": ["json", "pdf", "pptx"]})


def _user_is_admin(user):
    return user.is_superuser or getattr(user, "has_role", lambda r: False)("admin")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_cognition_dashboard(request):
    """GET /api/sessions/admin/cognition-dashboard/ — merged observability + cost."""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.product_observability import get_product_observability_dashboard
    from user_sessions.services.ai_cost_dashboard import get_ai_cost_dashboard
    from user_sessions.services.admin_cognition_api import get_workflow_usage_stats

    days = int(request.query_params.get("days", 7))
    from user_sessions.services.admin_cognition_api import get_live_cognition_metrics
    from user_sessions.services.product_signals import get_product_signals_dashboard

    return Response({
        "observability": get_product_observability_dashboard(),
        "cost": get_ai_cost_dashboard(days=days),
        "workflow_usage": get_workflow_usage_stats(days=days),
        "live": get_live_cognition_metrics(minutes=60),
        "product_signals": get_product_signals_dashboard(days=days),
        "system_health": __import__(
            "user_sessions.services.system_health", fromlist=["get_system_health"]
        ).get_system_health(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_cognition_live(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.admin_cognition_api import get_live_cognition_metrics

    minutes = min(int(request.query_params.get("minutes", 30)), 240)
    return Response(get_live_cognition_metrics(minutes=minutes))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_chunk_quality(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.chunk_quality_audit import audit_chunks

    limit = min(int(request.query_params.get("limit", 500)), 2000)
    return Response(audit_chunks(limit=limit))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_rag_dev_config(request):
    """GET/POST /api/sessions/admin/rag-dev/config/"""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.rag_dev_config import get_rag_dev_config, save_rag_dev_config

    if request.method == 'GET':
        return Response(get_rag_dev_config())

    payload = {
        "active_pipeline": str(request.data.get("active_pipeline", "rag_v1") or "rag_v1"),
        "enabled": bool(request.data.get("enabled", False)),
        "pre_retrieval_prompt": str(request.data.get("pre_retrieval_prompt", "") or ""),
        "system_injection_prompt": str(request.data.get("system_injection_prompt", "") or ""),
        "retrieval_profile_notes": str(request.data.get("retrieval_profile_notes", "") or ""),
        "phase_1_base_prompt": str(request.data.get("phase_1_base_prompt", "") or ""),
        "phase_1_admin_injection_prompt": str(request.data.get("phase_1_admin_injection_prompt", "") or ""),
        "phase_1_admin_injection_goal": str(request.data.get("phase_1_admin_injection_goal", "") or ""),
        "phase_1_admin_injection_criteria": str(request.data.get("phase_1_admin_injection_criteria", "") or ""),
        "phase_1_master_prompt": str(request.data.get("phase_1_master_prompt", "") or ""),
        "phase_2_master_prompt": str(request.data.get("phase_2_master_prompt", "") or ""),
        "phase_3_master_prompt": str(request.data.get("phase_3_master_prompt", "") or ""),
        "phase_4_master_prompt": str(request.data.get("phase_4_master_prompt", "") or ""),
    }

    saved = save_rag_dev_config(payload, updated_by=getattr(request.user, "email", "admin"))
    return Response(saved)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_rag_dev_index_status(request):
    """GET /api/sessions/admin/rag-dev/index-status/"""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    from utils.ai_knowledge_auto import (
        compute_knowledge_fingerprint,
        elasticsearch_index_exists,
        load_index_state,
        needs_rebuild,
    )

    should_rebuild, reason = needs_rebuild(force=False)
    state = load_index_state()
    index_exists = elasticsearch_index_exists()

    doc_count = None
    if index_exists:
        try:
            from document.utils.elasticsearch_service import ElasticsearchService
            from utils.ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME

            es = ElasticsearchService()
            doc_count = es.es.count(index=AI_KNOWLEDGE_INDEX_NAME).get("count")
        except Exception:
            doc_count = None

    return Response(
        {
            "index_exists": index_exists,
            "doc_count": doc_count,
            "needs_rebuild": should_rebuild,
            "reason": reason,
            "fingerprint": compute_knowledge_fingerprint(),
            "state": state,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_rag_dev_rebuild_index(request):
    """POST /api/sessions/admin/rag-dev/rebuild-index/"""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    from utils.ai_knowledge_auto import ensure_index_current

    force = bool(request.data.get("force", False))
    async_build = bool(request.data.get("async_build", True))
    ok, message = ensure_index_current(async_build=async_build, force=force)

    return Response(
        {
            "success": bool(ok),
            "message": message,
            "force": force,
            "async_build": async_build,
        },
        status=status.HTTP_200_OK if ok else status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_rag_dev_test_query(request):
    """POST /api/sessions/admin/rag-dev/test-query/"""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.rag_pipeline_resolver import generate_rag_response

    query = str(request.data.get("query") or "").strip()
    if not query:
        return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

    session = None
    session_id = request.data.get("session_id")
    if session_id:
        try:
            session = Session.objects.get(pk=int(session_id))
        except Exception:
            return Response({"detail": "Invalid session_id"}, status=status.HTTP_400_BAD_REQUEST)

    prompt_injection = {
        "pre_retrieval_prompt": str(request.data.get("pre_retrieval_prompt") or "").strip(),
        "system_injection_prompt": str(request.data.get("system_injection_prompt") or "").strip(),
    }

    result = generate_rag_response(
        query,
        user=request.user,
        session=session,
        session_id=getattr(session, "id", None),
        pipeline=str(request.data.get("pipeline") or "").strip() or None,
        agent_id=str(request.data.get("agent_id") or "strategist"),
        include_user_docs=bool(request.data.get("include_user_docs", False)),
        include_debug=True,
        include_evaluation=True,
        top_k=min(max(int(request.data.get("top_k", 8)), 1), 20),
        prompt_injection=prompt_injection,
    )

    return Response(
        {
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "chunks_retrieved": result.get("chunks_retrieved", 0),
            "retrieval_confidence": result.get("retrieval_confidence"),
            "retrieval_critique": result.get("retrieval_critique"),
            "retrieval_debug": result.get("retrieval_debug"),
            "active_pipeline": result.get("active_pipeline"),
            "rag_phase": result.get("rag_phase"),
            "phase_artifact": result.get("phase_artifact"),
            "phase_artifacts": result.get("phase_artifacts", {}),
            "evaluation": result.get("evaluation"),
            "latency_breakdown": result.get("latency_breakdown"),
            "reasoning_path": result.get("reasoning_path"),
            "discovery_metadata": (
                build_discovery_metadata(
                    session_id=str(getattr(session, "session_id", session.pk)),
                    q_id=f"Q{int(getattr(session, 'current_stage', 1) or 1)}",
                    raw_answer=query,
                )
                if session is not None
                else None
            ),
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_product_signals(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.product_signals import get_product_signals_dashboard

    days = int(request.query_params.get("days", 14))
    return Response(get_product_signals_dashboard(days=days))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_cognition_traces(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.admin_cognition_api import get_cognition_traces

    limit = min(int(request.query_params.get("limit", 50)), 200)
    return Response({"traces": get_cognition_traces(limit=limit)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_feedback_review(request):
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.admin_cognition_api import get_feedback_review

    limit = min(int(request.query_params.get("limit", 50)), 200)
    return Response({"items": get_feedback_review(limit=limit)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def demo_brands_catalog(request):
    """GET /api/sessions/demo-brands/ — investor/client demo catalog."""
    from user_sessions.services.demo_catalog import list_demo_brands

    return Response({"demos": list_demo_brands(), "one_click_label": "Generate Full Brand Intelligence Pack"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def session_demo_pack(request, pk):
    """POST /api/sessions/<pk>/demo-pack/ — instant demo pack (no Azure call)."""
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.demo_catalog import get_demo_pack
    from user_sessions.services.product_signals import record_product_signal

    demo_id = (request.data.get("demo_id") or "luxury").strip().lower()
    result = get_demo_pack(demo_id)
    if result.get("error"):
        return Response(result, status=status.HTTP_400_BAD_REQUEST)
    record_product_signal(session.id, "demo_pack", {"demo_id": demo_id})
    result["session_id"] = session.id
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_pilot_event(request, pk):
    """POST /api/sessions/<pk>/pilot-event/ — track pilot validation signals."""
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.product_signals import record_product_signal

    signal = (request.data.get("signal") or request.data.get("event") or "").strip()
    if not signal:
        return Response({"detail": "signal required"}, status=status.HTTP_400_BAD_REQUEST)
    meta = request.data.get("meta") or {}
    if request.data.get("workflow"):
        meta["workflow"] = request.data["workflow"]
    record_product_signal(session.id, signal, meta)
    return Response({"recorded": True, "signal": signal})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_pilot_kpis(request, pk):
    """GET /api/sessions/<pk>/pilot-kpis/ — session pilot validation metrics."""
    session = get_object_or_404(Session, pk=pk)
    if not session.has_access(request.user):
        return Response({"detail": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

    from user_sessions.services.pilot_kpis import get_session_pilot_kpis

    return Response(get_session_pilot_kpis(session.id))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_pilot_summary(request):
    """GET /api/sessions/pilot-summary/ — user-level pilot KPIs."""
    from user_sessions.services.pilot_kpis import get_user_pilot_summary

    days = int(request.query_params.get("days", 30))
    return Response(get_user_pilot_summary(request.user.id, days=days))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ops_intelligence(request):
    """GET /api/sessions/admin/ops-intelligence/ — AI ops layer."""
    if not _user_is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
    from user_sessions.services.admin_ops_intelligence import get_ops_intelligence

    days = int(request.query_params.get("days", 14))
    return Response(get_ops_intelligence(days=days))
