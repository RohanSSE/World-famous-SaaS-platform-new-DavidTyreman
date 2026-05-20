from django.urls import path
from .consumers import FoundationSummaryConsumer

websocket_urlpatterns = [
    path(
        "ws/sessions/<int:pk>/generate-foundation-summary/",
        FoundationSummaryConsumer.as_asgi()
    ),
]
