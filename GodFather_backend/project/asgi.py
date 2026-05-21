"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# application = get_asgi_application()



import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# 🔥 IMPORTANT: Initialize Django FIRST
django_asgi_app = get_asgi_application()

# ✅ Now it's safe to import Channels stuff
from channels.auth import AuthMiddlewareStack
from user_sessions.middleware import JWTAuthMiddleware
import user_sessions.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(user_sessions.routing.websocket_urlpatterns)
        )
    ),
})

