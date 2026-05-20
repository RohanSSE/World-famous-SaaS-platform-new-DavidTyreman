from django.urls import path
from .views import (
    task_dashboard, review_dashboard, agency_dashboard, user_dashboard, session_list, session_create, session_detail,
    session_start, session_complete, session_assign_agency,
    session_comments, session_add_comment, session_answers, session_answer_create, session_answers_batch,
    answer_detail, question_list, session_lock, session_unlock, session_generate_manifesto, session_manifesto,
    download_manifesto_pdf, answer_ai_suggestion, answer_ai_suggestion_draft, answer_ai_suggestion_from_documents,
    answer_ai_suggestion_unified, edit_conversation, session_conversations, session_generate_summary,
    session_generate_social_content,session_generate_foundation_summary,answer_ai_suggestions,
    assistant_suggestion,
    session_get_foundation_summary, session_update_foundation_summary

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


    # Social Media Content
    path('<int:pk>/generate-social-content/', session_generate_social_content, name='session_generate_social_content'),
    
    # NEW: Document-based suggestion endpoint
    path('sessions/<int:pk>/answer-ai-suggestion-from-documents/', answer_ai_suggestion_from_documents, name='answer-ai-suggestion-from-documents'),
    
]