# from django.db import models
# from django.conf import settings
# from django.utils import timezone
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from django.contrib.auth.hashers import make_password, check_password
# from accounts.models import Agency
# import uuid
# class Session(models.Model):
#     STATUS_CHOICES = [
#         ('draft', 'Draft'),
#         ('in_progress', 'In Progress'),
#         ('completed', 'Completed'),
#         ('locked', 'Locked'),  # New status for Brand Lock
#     ]
    
#     title = models.CharField(max_length=255, default='New Session')
#     created_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name='created_sessions',
#         on_delete=models.CASCADE,
#         help_text="User who created this session (usually client)"
#     )
#     agency = models.ForeignKey(
#             'accounts.Agency',
#             related_name='assigned_sessions',
#             null=True,
#             blank=True,
#             on_delete=models.SET_NULL,
#             help_text="Agency organization assigned to review this session"
#         )

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
#     is_locked = models.BooleanField(default=False, help_text="Brand Lock: Prevents edits without password")
#     locked_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name='locked_sessions',
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         help_text="User who locked the session"
#     )
#     locked_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when locked")
#     is_active = models.BooleanField(default=True)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.title} - {self.created_by.email}"
    
#     def has_access(self, user):
#         if user.is_superuser or user.has_role('admin'):
#             return True
#         if self.created_by == user:
#             return True
#         if self.agency and user.agency == self.agency and user.has_role('agency'):
#             return True
#         return False
    

#     def can_edit_answers(self, user):
#         """Check if user can edit answers - simple flag check"""
#         if user.is_superuser or user.has_role('admin'):
#             return True  # Admins bypass lock
#         if self.is_locked:
#             return False  # Locked sessions cannot be edited
#         if self.created_by == user and self.status not in ['locked']:
#             return True
#         return False

    

#     def can_delete(self, user):
#         if user.is_superuser or user.has_role('admin'):
#             return True
#         if self.created_by == user and self.status == 'draft' and not self.is_locked:
#             return True
#         return False


#     def can_review(self, user):
#         """Check if user can review this session"""
#         if user.is_superuser or user.has_role('admin'):
#             return True
#         # Any agency member can review if session assigned to their agency
#         if self.agency and user.agency == self.agency and user.has_role('agency'):
#             return True
#         return False


    
#     def get_progress(self):
#         total_questions = Question.objects.filter(is_active=True).count()
#         answered_questions = self.answers.count()
#         if total_questions == 0:
#             return 0
#         return (answered_questions / total_questions) * 100
    
#     def is_complete(self):
#         # Only Stage 1 (Foundation) questions are required for completion
#         required_questions = Question.objects.filter(
#             is_active=True, 
#             is_required=True,
#             stage=1  # Only check Foundation stage
#         )
#         answered_question_ids = self.answers.values_list('question_id', flat=True)
#         return all(q.id in answered_question_ids for q in required_questions)
    
#     def has_pending_feedback(self):
#         return self.review_comments.filter(is_resolved=False).exists()
    

#     def lock_session(self, user):
#         """Simple lock - toggle flag"""
#         if self.is_locked:
#             raise ValueError("Session already locked")
#         if self.created_by != user and not (user.is_superuser or user.has_role('admin')):
#             raise ValueError("Only creator or admin can lock")
        
#         self.is_locked = True
#         self.locked_by = user
#         self.locked_at = timezone.now()
#         self.status = 'locked'
#         self.save()
        
#         # Send notification
#         send_mail(
#             'Brand Session Locked',
#             f'Your session "{self.title}" has been locked by {user.email} to protect brand IP.',
#             'from@example.com',
#             [self.created_by.email],
#             fail_silently=True,
#         )
    

#     def unlock_session(self, user):
#         """Simple unlock - toggle flag"""
#         if not self.is_locked:
#             raise ValueError("Session is not locked")
#         if self.created_by != user and not (user.is_superuser or user.has_role('admin')):
#             raise ValueError("Only creator or admin can unlock")
        
#         self.is_locked = False
#         self.locked_by = None
#         self.locked_at = None
#         self.status = 'completed'
#         self.save()
        
#         # Send notification
#         send_mail(
#             'Brand Session Unlocked',
#             f'Session "{self.title}" has been unlocked by {user.email} for editing.',
#             'from@example.com',
#             [self.created_by.email],
#             fail_silently=True,
#         )


#     def get_current_stage(self):
#         """Get the current unlocked stage based on completed answers"""
#         for stage_num in range(1, 6):  # 5 stages
#             required_questions = Question.objects.filter(
#                 stage=stage_num,
#                 is_required=True,
#                 is_active=True
#             )
#             answered = self.answers.filter(
#                 question__in=required_questions
#             ).count()
            
#             if answered < required_questions.count():
#                 return stage_num  # This stage incomplete
        
#         return 6  # All stages complete


#     def can_access_stage(self, stage_num):
#         """Check if user can access a specific stage"""
#         return self.get_current_stage() >= stage_num


# class Question(models.Model):
#     CATEGORY_CHOICES = [
#         ('brand_identity', 'Brand Identity'),
#         ('target_audience', 'Target Audience'),
#         ('values', 'Values & Mission'),
#         ('messaging', 'Messaging'),
#         ('visual', 'Visual Identity'),
#         ('other', 'Other'),
#     ]

#     STAGE_CHOICES = [
#         (1, 'Foundation'),
#         (2, 'Identity'),
#     ]
    
#     text = models.TextField()
#     category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
#     stage = models.IntegerField(choices=STAGE_CHOICES, default=1)  # ADD THIS
#     order = models.IntegerField(default=0)
#     is_required = models.BooleanField(default=True)
#     is_active = models.BooleanField(default=True)
#     placeholder = models.CharField(max_length=255, blank=True, null=True)
#     help_text = models.TextField(blank=True, null=True)
#     visible_to_roles = models.JSONField(default=list, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['order', 'id']
    
#     def __str__(self):
#         return f"Q{self.order}: {self.text[:50]}"
    
#     def is_visible_to(self, user):
#         if not self.visible_to_roles:
#             return True
#         if user.is_superuser:
#             return True
#         user_role = user.get_role_name()
#         return user_role.lower() in [role.lower() for role in self.visible_to_roles]

# class Answer(models.Model):
#     session = models.ForeignKey(Session, on_delete=models.CASCADE,related_name='answers')
#     question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='answers_for_question' )
#     answer_text = models.TextField()
#     ai_suggestion = models.TextField(blank=True, null=True)
#     is_ai_accepted = models.BooleanField(default=False)
    
#     answered_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name='answers_given',
#         on_delete=models.SET_NULL,
#         null=True
#     )
#     version = models.IntegerField(default=1)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['question__order']
#         unique_together = ['session', 'question']
    
#     def save(self, *args, **kwargs):
#         if self.pk:
#             self.version += 1
#         super().save(*args, **kwargs)






# class Conversation(models.Model):
#     session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='conversations'  )
#     question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='conversations_for_question')
#     ROLE_CHOICES = [
#         ('user', 'User'),
#         ('assistant', 'Assistant'),
#     ]
#     role = models.CharField(max_length=20, choices=ROLE_CHOICES)
#     content = models.TextField(blank=True)  # Main text content
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['created_at']

#     def __str__(self):
#         return f"{self.role}: {self.content[:50]}"




# class ReviewComment(models.Model):
#     session = models.ForeignKey(Session, related_name='review_comments', on_delete=models.CASCADE)
#     answer = models.ForeignKey(Answer, related_name='review_comments', on_delete=models.CASCADE, null=True, blank=True)
#     comment = models.TextField()
#     is_resolved = models.BooleanField(default=False)
#     resolved_at = models.DateTimeField(null=True, blank=True)
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_comments_made')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def mark_resolved(self):
#         self.is_resolved = True
#         self.resolved_at = timezone.now()
#         self.save()

# # Signal for notification on feedback
# @receiver(post_save, sender=ReviewComment)
# def notify_on_feedback(sender, instance, created, **kwargs):
#     if created:
#         send_mail(
#             'New Feedback on Your Branding Session',
#             f'Feedback: {instance.comment}',
#             'from@example.com',
#             [instance.session.created_by.email],
#             fail_silently=False,
#         )




# class AIOutput(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('processing', 'Processing'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed'),
#     ]
    
#     session = models.OneToOneField(Session, related_name='ai_output', on_delete=models.CASCADE)
#     manifesto = models.TextField(blank=True, null=True)
#     json_output = models.JSONField(blank=True, null=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     error_message = models.TextField(blank=True, null=True)
#     generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='generated_outputs')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"AI Output for {self.session.title}"





# class FoundationSummary(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('processing', 'Processing'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed'),
#     ]

#     session = models.OneToOneField(
#         Session,
#         related_name='foundation_summary',
#         on_delete=models.CASCADE
#     )

#     summary_text = models.TextField(blank=True, null=True)

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='pending'
#     )

#     error_message = models.TextField(blank=True, null=True)

#     generated_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name='generated_foundation_summaries'
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Foundation Summary for {self.session.title}"







from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import Agency
import uuid
class Session(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),  # New status for Brand Lock
    ]
    
    title = models.CharField(max_length=255, default='New Session')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_sessions',
        on_delete=models.CASCADE,
        help_text="User who created this session (usually client)"
    )
    agency = models.ForeignKey(
            'accounts.Agency',
            related_name='assigned_sessions',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            help_text="Agency organization assigned to review this session"
        )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_locked = models.BooleanField(default=False, help_text="Brand Lock: Prevents edits without password")
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='locked_sessions',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="User who locked the session"
    )
    locked_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when locked")
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.created_by.email}"
    
    def has_access(self, user):
        if user.is_superuser or user.has_role('admin'):
            return True
        if self.created_by == user:
            return True
        if self.agency and user.agency == self.agency and user.has_role('agency'):
            return True
        return False
    

    def can_edit_answers(self, user):
        """Check if user can edit answers - simple flag check"""
        if user.is_superuser or user.has_role('admin'):
            return True  # Admins bypass lock
        if self.is_locked:
            return False  # Locked sessions cannot be edited
        if self.created_by == user and self.status not in ['locked']:
            return True
        return False

    

    def can_delete(self, user):
        if user.is_superuser or user.has_role('admin'):
            return True
        if self.created_by == user and self.status == 'draft' and not self.is_locked:
            return True
        return False


    def can_review(self, user):
        """Check if user can review this session"""
        if user.is_superuser or user.has_role('admin'):
            return True
        # Any agency member can review if session assigned to their agency
        if self.agency and user.agency == self.agency and user.has_role('agency'):
            return True
        return False


    
    def get_progress(self):
        total_questions = Question.objects.filter(is_active=True).count()
        answered_questions = self.answers.count()
        if total_questions == 0:
            return 0
        return (answered_questions / total_questions) * 100
    
    # def is_complete(self):
    #     # Only Stage 1 (Foundation) questions are required for completion
    #     required_questions = Question.objects.filter(
    #         is_active=True, 
    #         is_required=True,
    #         stage=1  # Only check Foundation stage
    #     )
    #     answered_question_ids = self.answers.values_list('question_id', flat=True)
    #     return all(q.id in answered_question_ids for q in required_questions)

    def is_complete(self):
    # Require stages 1, 2, 3 (Basic, Foundation, Identity)
        required_questions = Question.objects.filter(
        is_active=True,
        is_required=True,
        stage__in=[1, 2, 3]
        )
        answered_question_ids = set(self.answers.values_list('question_id', flat=True))
        return all(q.id in answered_question_ids for q in required_questions)



    
    def has_pending_feedback(self):
        return self.review_comments.filter(is_resolved=False).exists()
    

    def lock_session(self, user):
        """Simple lock - toggle flag"""
        if self.is_locked:
            raise ValueError("Session already locked")
        if self.created_by != user and not (user.is_superuser or user.has_role('admin')):
            raise ValueError("Only creator or admin can lock")
        
        self.is_locked = True
        self.locked_by = user
        self.locked_at = timezone.now()
        self.status = 'locked'
        self.save()
        
        # Send notification
        send_mail(
            'Brand Session Locked',
            f'Your session "{self.title}" has been locked by {user.email} to protect brand IP.',
            'from@example.com',
            [self.created_by.email],
            fail_silently=True,
        )
    

    def unlock_session(self, user):
        """Simple unlock - toggle flag"""
        if not self.is_locked:
            raise ValueError("Session is not locked")
        if self.created_by != user and not (user.is_superuser or user.has_role('admin')):
            raise ValueError("Only creator or admin can unlock")
        
        self.is_locked = False
        self.locked_by = None
        self.locked_at = None
        self.status = 'completed'
        self.save()
        
        # Send notification
        send_mail(
            'Brand Session Unlocked',
            f'Session "{self.title}" has been unlocked by {user.email} for editing.',
            'from@example.com',
            [self.created_by.email],
            fail_silently=True,
        )


    def get_current_stage(self):
        """
        Stage flow:
        1 = Basic
        2 = Foundation
        3 = Identity
        4 = More
        """
        for stage_num in range(1, 5):  # 4 stages
            required_questions = Question.objects.filter(
                stage=stage_num,
                is_required=True,
                is_active=True
            )

            if not required_questions.exists():
                continue

            answered = self.answers.filter(
                question__in=required_questions
            ).count()

            if answered < required_questions.count():
                return stage_num  # This stage is incomplete

        return 5  # All stages complete


    def can_access_stage(self, stage_num):
        """Check if user can access a specific stage"""
        return self.get_current_stage() >= stage_num


class Question(models.Model):
    CATEGORY_CHOICES = [
        ('brand_identity', 'Brand Identity'),
        ('target_audience', 'Target Audience'),
        ('values', 'Values & Mission'),
        ('messaging', 'Messaging'),
        ('visual', 'Visual Identity'),
        ('other', 'Other'),
    ]

    STAGE_CHOICES = [
    (1, 'Basic'),
    (2, 'Foundation'),
    (3, 'Identity'),
    (4, 'More'),
    ]

    
    text = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    stage = models.IntegerField(choices=STAGE_CHOICES, default=1)  # ADD THIS
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.TextField(blank=True, null=True)
    visible_to_roles = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"
    
    def is_visible_to(self, user):
        if not self.visible_to_roles:
            return True
        if user.is_superuser:
            return True
        user_role = user.get_role_name()
        return user_role.lower() in [role.lower() for role in self.visible_to_roles]

class Answer(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE,related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='answers_for_question' )
    answer_text = models.TextField()
    ai_suggestion = models.TextField(blank=True, null=True)
    is_ai_accepted = models.BooleanField(default=False)
    
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='answers_given',
        on_delete=models.SET_NULL,
        null=True
    )
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['question__order']
        unique_together = ['session', 'question']
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)






class Conversation(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='conversations'  )
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='conversations_for_question')
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)  # Main text content
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"




class ReviewComment(models.Model):
    session = models.ForeignKey(Session, related_name='review_comments', on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, related_name='review_comments', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_comments_made')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_resolved(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

# Signal for notification on feedback
@receiver(post_save, sender=ReviewComment)
def notify_on_feedback(sender, instance, created, **kwargs):
    if created:
        send_mail(
            'New Feedback on Your Branding Session',
            f'Feedback: {instance.comment}',
            'from@example.com',
            [instance.session.created_by.email],
            fail_silently=False,
        )




class AIOutput(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    session = models.OneToOneField(Session, related_name='ai_output', on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True, null=True)
    json_output = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='generated_outputs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"AI Output for {self.session.title}"





class FoundationSummary(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    session = models.OneToOneField(
        Session,
        related_name='foundation_summary',
        on_delete=models.CASCADE
    )

    summary_text = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    error_message = models.TextField(blank=True, null=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_foundation_summaries'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Foundation Summary for {self.session.title}"