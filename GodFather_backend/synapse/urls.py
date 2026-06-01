from django.urls import path

from synapse.views import (
    SynapseAnswerAPIView,
    SynapseAnswerStatusAPIView,
    SynapseSessionDetailAPIView,
    SynapseSessionStartAPIView,
)

urlpatterns = [
    path("session/start/", SynapseSessionStartAPIView.as_view(), name="synapse-session-start"),
    path("session/<str:session_id>/", SynapseSessionDetailAPIView.as_view(), name="synapse-session-detail"),
    path("answer/", SynapseAnswerAPIView.as_view(), name="synapse-answer"),
    path("answer/status/<str:task_id>/", SynapseAnswerStatusAPIView.as_view(), name="synapse-answer-status"),
]
