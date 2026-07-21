# Generated manually for ORB turn audit logging.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user_sessions', '0026_rename_user_sessio_section_3f5964_idx_user_sessio_section_639858_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrbTurnAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_email', models.EmailField(blank=True, db_index=True, default='', max_length=254)),
                ('conversation_id_snapshot', models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ('turn_index', models.PositiveIntegerField(db_index=True, default=1)),
                ('conversation_question_id', models.PositiveIntegerField(blank=True, db_index=True, null=True)),
                ('question_text', models.TextField(blank=True, default='')),
                ('latest_answer', models.TextField(blank=True, default='')),
                ('previous_score', models.IntegerField(blank=True, null=True)),
                ('delta_score', models.IntegerField(blank=True, null=True)),
                ('confidence_score', models.IntegerField(blank=True, null=True)),
                ('target_confidence_threshold', models.IntegerField(blank=True, null=True)),
                ('answer_preview', models.TextField(blank=True, default='')),
                ('response_preview', models.TextField(blank=True, default='')),
                ('status', models.CharField(blank=True, db_index=True, default='', max_length=32)),
                ('associated_discovery_id', models.CharField(blank=True, db_index=True, default='', max_length=128)),
                ('view_api_response', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('guardrail', models.JSONField(blank=True, default=dict)),
                ('crux_context', models.JSONField(blank=True, default=dict)),
                ('confidence_tracking', models.JSONField(blank=True, default=dict)),
                ('conversation_dropped', models.BooleanField(default=False)),
                ('source', models.CharField(blank=True, default='edit_conversation_orb', max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orb_turn_audit_logs', to='user_sessions.conversation')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orb_turn_audit_logs', to='user_sessions.question')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orb_turn_audit_logs', to='user_sessions.session')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orb_turn_audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user_email', '-created_at'], name='user_sessio_user_em_83f8bb_idx'),
                    models.Index(fields=['user', '-created_at'], name='user_sessio_user_id_3e7f45_idx'),
                    models.Index(fields=['session', '-created_at'], name='user_sessio_session_18042a_idx'),
                    models.Index(fields=['question', '-created_at'], name='user_sessio_questio_3d82b8_idx'),
                    models.Index(fields=['associated_discovery_id', 'turn_index'], name='user_sessio_assoc__d3077e_idx'),
                    models.Index(fields=['status', '-created_at'], name='user_sessio_status_86f8fe_idx'),
                ],
            },
        ),
    ]
