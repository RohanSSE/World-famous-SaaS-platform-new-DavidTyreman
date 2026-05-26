from django.contrib import admin
from django.utils.html import format_html
from .models import Session, Question, Answer, ReviewComment, AIOutput, FoundationSummary

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by_email', 'agency_name', 'status_badge', 'lock_badge', 'progress_bar', 'pending_feedback_badge', 'created_at']
    list_filter = ['status', 'is_locked', 'is_active', 'created_at']
    search_fields = ['title', 'created_by__email', 'agency__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'locked_at', 'progress_display', 'lock_display']
    
    fieldsets = (
        ('Session Info', {'fields': ('title', 'status', 'is_active', 'is_locked')}),
        ('Users', {'fields': ('created_by', 'agency', 'locked_by')}),  # Changed assigned_to to agency
        ('Brand Lock', {'fields': ('lock_display',)}),
        ('Progress', {'fields': ('progress_display',)}),
        ('Timestamps', {'fields': ('completed_at', 'locked_at', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def created_by_email(self, obj):
        return obj.created_by.email
    created_by_email.short_description = 'Client'
    

    def agency_name(self, obj):
        return obj.agency.name if obj.agency else '-'
    agency_name.short_description = 'Agency'
    
    def status_badge(self, obj):
        colors = {'draft': '#9e9e9e', 'in_progress': '#2196f3', 'completed': '#ff9800', 'locked': '#4caf50'}
        return format_html('<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                           colors.get(obj.status, '#9e9e9e'), obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def lock_badge(self, obj):
        if obj.is_locked:
            return format_html('<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 10px; font-weight: bold;">Locked by {} on {}</span>', 
                               obj.locked_by.email if obj.locked_by else 'Admin', obj.locked_at.strftime('%Y-%m-%d') if obj.locked_at else 'N/A')
        return format_html('<span style="color: #9e9e9e;">Unlocked</span>')
    lock_badge.short_description = 'Brand Lock'
    
    def pending_feedback_badge(self, obj):
        count = obj.review_comments.filter(is_resolved=False).count()
        if count > 0:
            return format_html('<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 10px; font-weight: bold;">{}</span>', count)
        return format_html('<span style="color: #4caf50;">✓</span>')
    pending_feedback_badge.short_description = 'Feedback'
    
    def progress_bar(self, obj):
        progress = obj.get_progress()
        color = '#4caf50' if progress == 100 else '#2196f3'
        return format_html('<div style="width: 100px; background-color: #e0e0e0; border-radius: 5px;"><div style="width: {}%; background-color: {}; height: 20px; border-radius: 5px; text-align: center; color: white; font-size: 11px; line-height: 20px;">{}%</div></div>',
                           progress, color, progress)
    progress_bar.short_description = 'Progress'
    
    def progress_display(self, obj):
        progress = obj.get_progress()
        answered = obj.answers.count()
        total = Question.objects.filter(is_active=True).count()
        return format_html('<strong>Progress:</strong> {:.1f}%<br><strong>Answered:</strong> {} / {} questions<br><strong>Pending Feedback:</strong> {}',
                           progress, answered, total, obj.review_comments.filter(is_resolved=False).count())
    progress_display.short_description = 'Session Progress'
    

    def lock_display(self, obj):
        if obj.is_locked:
            return format_html('<strong>Status:</strong> Locked<br><strong>By:</strong> {}<br><strong>On:</strong> {}<br><strong>Action:</strong> Use unlock to edit',
                            obj.locked_by.email if obj.locked_by else 'Admin', obj.locked_at.strftime('%Y-%m-%d %H:%M') if obj.locked_at else 'N/A')
        return "Unlocked"
    lock_display.short_description = 'Lock Details'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'text_short', 'category', 'is_required_badge', 'is_active_badge', 'created_at']
    list_filter = ['category', 'is_required', 'is_active', 'created_at']
    search_fields = ['text', 'help_text']
    ordering = ['order', 'id']
    
    def text_short(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_short.short_description = 'Question Text'
    
    def is_required_badge(self, obj):
        if obj.is_required:
            return format_html('<span style="color: #f44336; font-weight: bold;">●</span> Required')
        return format_html('<span style="color: #9e9e9e;">○</span> Optional')
    is_required_badge.short_description = 'Required'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">●</span> Active')
        return format_html('<span style="color: red; font-weight: bold;">●</span> Inactive')
    is_active_badge.short_description = 'Status'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_title', 'question_short', 'answer_short', 'version', 'has_feedback_badge', 'created_at']
    list_filter = ['is_ai_accepted', 'created_at']
    search_fields = ['answer_text', 'ai_suggestion', 'session__title', 'question__text']
    readonly_fields = ['created_at', 'updated_at', 'version']
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = 'Session'
    
    def question_short(self, obj):
        text = obj.question.text
        return text[:40] + '...' if len(text) > 40 else text
    question_short.short_description = 'Question'
    
    def answer_short(self, obj):
        text = obj.answer_text
        return text[:50] + '...' if len(text) > 50 else text
    answer_short.short_description = 'Answer'
    
    def has_feedback_badge(self, obj):
        count = obj.review_comments.filter(is_resolved=False).count()
        if count > 0:
            return format_html('<span style="background-color: #ff9800; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">{}</span>', count)
        return format_html('<span style="color: #4caf50;">✓</span>')
    has_feedback_badge.short_description = 'Feedback'

@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_title', 'answer_question', 'comment_short', 'created_by_email', 'is_resolved_badge', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['comment', 'session__title', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = 'Session'
    
    def answer_question(self, obj):
        if obj.answer:
            return obj.answer.question.text[:40] + '...'
        return 'General comment'
    answer_question.short_description = 'Question'
    
    def comment_short(self, obj):
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
    comment_short.short_description = 'Comment'
    
    def created_by_email(self, obj):
        return obj.created_by.email
    created_by_email.short_description = 'By'
    
    def is_resolved_badge(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: #4caf50; font-weight: bold;">✓</span> Resolved')
        return format_html('<span style="color: #ff9800; font-weight: bold;">○</span> Pending')
    is_resolved_badge.short_description = 'Status'



@admin.register(AIOutput)
class AIOutputAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_title', 'status_badge', 'has_manifesto', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['session__title', 'manifesto']
    readonly_fields = ['created_at', 'updated_at']
    
    def session_title(self, obj):
        return obj.session.title
    session_title.short_description = 'Session'
    
    def status_badge(self, obj):
        colors = {'pending': '#9e9e9e', 'processing': '#2196f3', 'completed': '#4caf50', 'failed': '#f44336'}
        return format_html('<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                           colors.get(obj.status, '#9e9e9e'), obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def has_manifesto(self, obj):
        if obj.manifesto:
            return format_html('<span style="color: green; font-weight: bold;">✓</span> Yes')
        return format_html('<span style="color: #9e9e9e;">-</span> No')
    has_manifesto.short_description = 'Manifesto'

    
admin.site.register(FoundationSummary)

from .models import Conversation, RAGQueryLog, AIUsageLog, EvaluationRun, EvaluationResult
admin.site.register(Conversation)


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = (
        "id", "agent_id", "endpoint", "total_tokens", "estimated_cost_usd",
        "latency_ms", "cache_hit", "degraded", "user", "created_at",
    )
    list_filter = ("agent_id", "cache_hit", "degraded", "created_at")
    readonly_fields = ("created_at",)

    def changelist_view(self, request, extra_context=None):
        from user_sessions.services.ai_cost_dashboard import get_ai_cost_dashboard

        extra_context = extra_context or {}
        extra_context["cost_dashboard"] = get_ai_cost_dashboard(days=7)
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = (
        "id", "run_type", "status", "passed_cases", "total_cases",
        "avg_groundedness", "avg_hallucination_risk", "created_at",
    )
    list_filter = ("run_type", "status", "created_at")
    readonly_fields = ("summary",)


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ("case_id", "run", "passed", "groundedness", "hallucination_risk", "citation_accuracy")
    list_filter = ("passed", "run")


@admin.register(RAGQueryLog)
class RAGQueryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "agent_id", "query_preview", "latency_ms", "cache_hit", "user", "created_at")
    list_filter = ("agent_id", "cache_hit", "created_at")
    search_fields = ("query",)
    readonly_fields = ("top_chunks", "debug_payload", "token_usage")

    def query_preview(self, obj):
        return obj.query[:80]
    query_preview.short_description = "Query"
