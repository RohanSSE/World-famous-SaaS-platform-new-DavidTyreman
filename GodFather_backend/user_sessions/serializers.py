
from rest_framework import serializers
from .models import Session, Answer, Question, ReviewComment, AIOutput, Conversation
from accounts.serializers import UserSerializer, AgencySerializer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'category', 'stage', 'order', 'is_required', 'is_active', 'placeholder', 'help_text', 'visible_to_roles', 'created_at', 'updated_at']  # ADD 'stage'
        read_only_fields = ['id', 'created_at', 'updated_at']
        ref_name = 'BrandProfileQuestionSerializer'

class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_order = serializers.IntegerField(source='question.order', read_only=True)
    answered_by_email = serializers.EmailField(source='answered_by.email', read_only=True, allow_null=True)
    has_feedback = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = ['id', 'session', 'question', 'question_text', 'question_order', 'answer_text', 'ai_suggestion', 'is_ai_accepted', 
                  'answered_by', 'answered_by_email', 'version', 'has_feedback', 'feedback_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'ai_suggestion', 'answered_by', 'version', 'created_at', 'updated_at']
        ref_name = 'UserSessionsAnswerSerializer'

    def get_has_feedback(self, obj):
        return obj.review_comments.filter(is_resolved=False).exists()
    
    def get_feedback_count(self, obj):
        return obj.review_comments.filter(is_resolved=False).count()


class AnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'answer_text']
    
    # def validate_answer_text(self, value):
    #     if not value or len(value.strip()) < 3:
    #         raise serializers.ValidationError('Answer must be at least 3 characters long.')
    #     return value.strip()


class ReviewCommentSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_role = serializers.CharField(source='created_by.get_role_name', read_only=True)
    
    class Meta:
        model = ReviewComment
        fields = ['id', 'session', 'comment', 'is_resolved', 'resolved_at',
                  'created_by', 'created_by_email', 'created_by_role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'session', 'created_by', 'is_resolved', 'resolved_at', 'created_at', 'updated_at']

    # Force session-level (no answer tie-in)
    def create(self, validated_data):
        validated_data['answer'] = None
        return super().create(validated_data)

        

class SessionListSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_role = serializers.CharField(source='created_by.get_role_name', read_only=True)
    agency_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    answered_questions = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    pending_feedback = serializers.SerializerMethodField()
    is_locked_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'created_by', 'created_by_email', 'created_by_role', 'agency', 'agency_name',
          'status', 'is_locked', 'is_locked_display', 'locked_by', 'locked_at', 
          'progress', 'answered_questions', 'total_questions', 'pending_feedback', 
          'is_active', 'completed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_progress(self, obj):
        return round(obj.get_progress(), 2)
    
    def get_answered_questions(self, obj):
        return obj.answers.count()
    
    def get_total_questions(self, obj):
        return Question.objects.filter(is_active=True).count()
    
    def get_pending_feedback(self, obj):
        return obj.review_comments.filter(is_resolved=False).count()
    
    def get_agency_name(self, obj):
        return obj.agency.name if obj.agency else None
    
    def get_is_locked_display(self, obj):
        if obj.is_locked:
            return f"Locked by {obj.locked_by.email} on {obj.locked_at.strftime('%Y-%m-%d %H:%M')}" if obj.locked_by else "Locked"
        return "Unlocked"

class SessionDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    agency = AgencySerializer(read_only=True, allow_null=True)
    answers = AnswerSerializer(many=True, read_only=True)
    review_comments = ReviewCommentSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()
    has_ai_output = serializers.SerializerMethodField()
    can_edit_answers = serializers.SerializerMethodField()
    pending_feedback_count = serializers.SerializerMethodField()
    is_locked_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'created_by', 'agency',
                  'status', 'is_locked', 'is_locked_display', 'locked_by', 'locked_at', 
                  'is_active', 'answers', 'review_comments',
                  'progress', 'is_complete', 'has_ai_output', 'can_edit_answers', 
                  'pending_feedback_count',
                  'completed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_progress(self, obj):
        return round(obj.get_progress(), 2)
    
    def get_is_complete(self, obj):
        return obj.is_complete()
    
    def get_has_ai_output(self, obj):
        return hasattr(obj, 'ai_output')
    
    def get_can_edit_answers(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.can_edit_answers(request.user)
        return False
    
    def get_pending_feedback_count(self, obj):
        return obj.review_comments.filter(is_resolved=False).count()
    
    def get_is_locked_display(self, obj):
        if obj.is_locked:
            return f"Locked by {obj.locked_by.email} on {obj.locked_at.strftime('%Y-%m-%d %H:%M')}" if obj.locked_by else "Locked"
        return "Unlocked"

# Multiple Sessions
class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['title', 'agency']
    
    # def validate_title(self, value):
    #     if not value or len(value.strip()) < 3:
    #         raise serializers.ValidationError('Title must be at least 3 characters long.')
    #     return value.strip()

# Single Session
class SessionCreateSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['title', 'agency']
    
    # def validate_title(self, value):
    #     if not value or len(value.strip()) < 3:
    #         raise serializers.ValidationError('Title must be at least 3 characters long.')
    #     return value.strip()
    
    def validate(self, data):
        user = self.context['request'].user
        # SINGLE MODE: Block if active session exists
        if Session.objects.filter(created_by=user, status__in=['draft', 'in_progress']).exists():
            raise serializers.ValidationError(
                "Single session mode: You already have an active session. Please complete or lock it before starting a new one."
            )
        return data



class AIOutputSerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source='session.title', read_only=True)
    generated_by_email = serializers.EmailField(source='generated_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AIOutput
        fields = ['id', 'session', 'session_title', 'manifesto', 'json_output', 'status', 'error_message',
                  'generated_by', 'generated_by_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'generated_by', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Prioritize json_output in the response
        if instance.json_output:
            representation['data'] = instance.json_output
        return representation


class ConversationSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'session', 'question', 'question_text', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']
