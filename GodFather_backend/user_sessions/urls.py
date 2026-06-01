from django.urls import path
from .views import (
    task_dashboard, review_dashboard, agency_dashboard, user_dashboard, session_list, session_create, session_detail,
    session_start, session_complete, session_assign_agency,
    session_comments, session_add_comment, session_answers, session_answer_create, session_answers_batch,
    answer_detail, question_list, session_lock, session_unlock, session_generate_manifesto, session_manifesto,
    download_manifesto_pdf, answer_ai_suggestion, answer_ai_suggestion_draft, answer_ai_suggestion_from_documents,
    answer_ai_suggestion_unified, edit_conversation, session_conversations, session_generate_summary,
    session_generate_social_content,session_generate_foundation_summary,answer_ai_suggestions,
    assistant_suggestion, brand_book_heading_insight,
    session_get_foundation_summary, session_update_foundation_summary,
    admin_questions_bulk_set,
    rag_query, ai_task_status, rag_query_stream, rag_agents_list,
    rag_system_health, ai_cost_dashboard,
    session_brand_brain, session_feedback_learning, session_brand_workflow,
    session_longitudinal_memory, brand_workflows_catalog,
    product_observability_dashboard, session_brand_export,
    admin_cognition_dashboard, admin_cognition_traces, admin_feedback_review,
    admin_cognition_live, admin_chunk_quality, admin_product_signals,
    demo_brands_catalog, session_demo_pack, record_pilot_event,
    session_pilot_kpis, user_pilot_summary, admin_ops_intelligence,

)

app_name = 'user_sessions'
urlpatterns = [
    # Dashboards
    path('dashboard/task/', task_dashboard, name='client_dashboard'),
    path('dashboard/review/', review_dashboard, name='agency_dashboard'),
    path('dashboard/agency/', agency_dashboard, name='agency_dashboard_full'),
    path('dashboard/user/', user_dashboard, name='user_dashboard_full'),

    path('', session_list, name='session_list'),

    path('create/', session_create, name='session_create'),

    path('<int:pk>/', session_detail, name='session_detail'),
    path('<int:pk>/start/', session_start, name='session_start'),
    path('<int:pk>/complete/', session_complete, name='session_complete'),
    path('<int:pk>/assign-agency/', session_assign_agency, name='session_assign_agency'),
    path('<int:pk>/lock/', session_lock, name='session_lock'),  # New for Brand Lock
    path('<int:pk>/unlock/', session_unlock, name='session_unlock'),  # New for Brand Lock
    
    # Comments
    path('<int:pk>/comments/', session_comments, name='session_comments'),
    path('<int:pk>/comments/add/', session_add_comment, name='session_add_comment'),
    
    # Answers
    path('<int:pk>/answers/', session_answers, name='session_answers'),
    path('<int:pk>/answers/create/', session_answer_create, name='session_answer_create'),
    path('<int:pk>/answers/batch/', session_answers_batch, name='session_answers_batch'),
    path('<int:pk>/answers/<int:answer_id>/', answer_detail, name='answer_detail'),
    path('<int:pk>/assistant-suggestion/', assistant_suggestion, name='assistant_suggestion'),

    path('<int:pk>/answers/<int:answer_id>/ai-suggestion/', answer_ai_suggestion, name='answer_ai_suggestion'),
    path('sessions/<int:pk>/ai-suggestion/draft/', answer_ai_suggestion_draft, name='ai_suggestion_draft'),
    
    # Conversations
    path('<int:pk>/conversations/', session_conversations, name='session_conversations'),
    path('<int:pk>/conversations/<int:conversation_id>/edit/', edit_conversation, name='edit_conversation'),
    # Questions
    path('questions/', question_list, name='question_list'),

    # Admin: bulk replace questions for stage counts
    path('admin/questions/bulk-set/', admin_questions_bulk_set, name='admin_questions_bulk_set'),


    # AI Manifesto
    path('<int:pk>/generate-manifesto/', session_generate_manifesto, name='session_generate_manifesto'),
    path('<int:pk>/manifesto/', session_manifesto, name='session_manifesto'),
    path('<int:pk>/manifesto/download/', download_manifesto_pdf, name='download_manifesto_pdf'),
    
    # Session Summary
    path('<int:pk>/generate-summary/', session_generate_summary, name='session_generate_summary'),
    
    # Foundation Summary
    path('<int:pk>/generate-foundation-summary/', session_generate_foundation_summary, name='session_foundation_generate_summary'),
    

    #Get foundation summary
    path("<int:pk>/foundation-summary/", session_get_foundation_summary, name="get-foundation-summary"),

    #Edit foundation summary
    path("<int:pk>/update-foundation-summary/", session_update_foundation_summary, name="update-foundation-summary"),

    # AI Answer suggestions (user types 2–3 words for manifesto)
    path('<int:pk>/ai-answer-suggestions/', answer_ai_suggestions, name='ai-answer-suggestions'),
    path('<int:pk>/brand-book-insight/', brand_book_heading_insight, name='brand-book-insight'),


    # Social Media Content
    path('<int:pk>/generate-social-content/', session_generate_social_content, name='session_generate_social_content'),
    
    # NEW: Document-based suggestion endpoint
    path('sessions/<int:pk>/answer-ai-suggestion-from-documents/', answer_ai_suggestion_from_documents, name='answer-ai-suggestion-from-documents'),

    # RAG query + Celery task polling (Phase 1–13)
    path('rag-query/', rag_query, name='rag-query-global'),
    path('<int:pk>/rag-query/', rag_query, name='rag-query'),
    path('rag-query/stream/', rag_query_stream, name='rag-query-stream-global'),
    path('<int:pk>/rag-query/stream/', rag_query_stream, name='rag-query-stream'),
    path('rag-agents/', rag_agents_list, name='rag-agents'),
    path('rag-system-health/', rag_system_health, name='rag-system-health'),
    path('ai-cost-dashboard/', ai_cost_dashboard, name='ai-cost-dashboard'),
    path('ai-tasks/<str:task_id>/', ai_task_status, name='ai-task-status'),

    # Brand operating system (productization — architecture frozen)
    path('brand-workflows/', brand_workflows_catalog, name='brand-workflows-catalog'),
    path('product-observability/', product_observability_dashboard, name='product-observability'),
    path('admin/cognition-dashboard/', admin_cognition_dashboard, name='admin-cognition-dashboard'),
    path('admin/cognition-traces/', admin_cognition_traces, name='admin-cognition-traces'),
    path('admin/feedback-review/', admin_feedback_review, name='admin-feedback-review'),
    path('admin/cognition-live/', admin_cognition_live, name='admin-cognition-live'),
    path('admin/chunk-quality/', admin_chunk_quality, name='admin-chunk-quality'),
    path('admin/product-signals/', admin_product_signals, name='admin-product-signals'),
    path('admin/ops-intelligence/', admin_ops_intelligence, name='admin-ops-intelligence'),
    path('demo-brands/', demo_brands_catalog, name='demo-brands-catalog'),
    path('pilot-summary/', user_pilot_summary, name='user-pilot-summary'),
    path('<int:pk>/brand-brain/', session_brand_brain, name='session-brand-brain'),
    path('<int:pk>/feedback-learning/', session_feedback_learning, name='session-feedback-learning'),
    path('<int:pk>/brand-workflow/', session_brand_workflow, name='session-brand-workflow'),
    path('<int:pk>/longitudinal-memory/', session_longitudinal_memory, name='session-longitudinal-memory'),
    path('<int:pk>/brand-export/', session_brand_export, name='session-brand-export'),
    path('<int:pk>/demo-pack/', session_demo_pack, name='session-demo-pack'),
    path('<int:pk>/pilot-event/', record_pilot_event, name='record-pilot-event'),
    path('<int:pk>/pilot-kpis/', session_pilot_kpis, name='session-pilot-kpis'),
]