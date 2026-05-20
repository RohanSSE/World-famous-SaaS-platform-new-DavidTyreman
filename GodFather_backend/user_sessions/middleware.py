from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        scope["user"] = AnonymousUser()

        auth_header = headers.get(b'authorization', None)

        if auth_header:
            try:
                auth_str = auth_header.decode()
                if auth_str.startswith("Bearer "):
                    token = auth_str.split(" ")[1]

                    user = await self.get_user_from_token(token)
                    if user:
                        scope["user"] = user
            except Exception as e:
                print("JWT WS auth error:", e)

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
        except Exception:
            return None
