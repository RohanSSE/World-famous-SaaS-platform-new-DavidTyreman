from django.urls import path

from brandgodfather.views import (
    BrandGodFatherAnswerAPIView,
    BrandGodFatherAnswerStatusAPIView,
    BrandGodFatherOutputCampaignAPIView,
    BrandGodFatherOutputOutreachAPIView,
    BrandGodFatherOutputSocialAPIView,
    BrandGodFatherSessionDetailAPIView,
    BrandGodFatherSessionStartAPIView,
)

urlpatterns = [
    path("session/start/", BrandGodFatherSessionStartAPIView.as_view(), name="brandgodfather-session-start"),
    path("session/<str:session_id>/", BrandGodFatherSessionDetailAPIView.as_view(), name="brandgodfather-session-detail"),
    path("answer/", BrandGodFatherAnswerAPIView.as_view(), name="brandgodfather-answer"),
    path("answer/status/<str:task_id>/", BrandGodFatherAnswerStatusAPIView.as_view(), name="brandgodfather-answer-status"),
    path("output/<str:session_id>/social/", BrandGodFatherOutputSocialAPIView.as_view(), name="brandgodfather-output-social"),
    path("output/<str:session_id>/campaign/", BrandGodFatherOutputCampaignAPIView.as_view(), name="brandgodfather-output-campaign"),
    path("output/<str:session_id>/outreach/", BrandGodFatherOutputOutreachAPIView.as_view(), name="brandgodfather-output-outreach"),
]
