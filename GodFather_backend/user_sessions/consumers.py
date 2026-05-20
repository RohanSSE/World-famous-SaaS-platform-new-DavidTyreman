# import json
# import logging
# from channels.generic.websocket import AsyncWebsocketConsumer
# from django.shortcuts import get_object_or_404
# from asgiref.sync import sync_to_async
# from openai import OpenAI
# logger = logging.getLogger(__name__)
# client = OpenAI()
# from user_sessions.models import Session, Answer
# # import your openai client
# # from .openai_client import openai_client


# class FoundationSummaryConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.session_id = self.scope["url_route"]["kwargs"]["pk"]

#         # # (Optional) Auth check
#         # user = self.scope["user"]
#         # if not user.is_authenticated:
#         #     await self.close(code=4001)
#         #     return

#         await self.accept()

#         # Start generation automatically on connect
#         await self.generate_summary()

#     async def disconnect(self, close_code):
#         pass

#     @sync_to_async
#     def get_qa_text(self):
#         session = get_object_or_404(Session, pk=self.session_id)

#         # You can keep your has_access check here if needed
#         # if not session.has_access(self.scope["user"]): raise Exception("Access denied")

#         answers = Answer.objects.filter(
#             session=session,
#             question__stage=1,
#             question__is_active=True
#         ).select_related("question").order_by("question__order")

#         if not answers.exists():
#             return None

#         qa_text = ""
#         for answer in answers:
#             qa_text += f"Q: {answer.question.text.strip()}\n"
#             qa_text += f"A: {answer.answer_text.strip()}\n\n"

#         return qa_text

#     async def generate_summary(self):
#         try:
#             qa_text = await self.get_qa_text()
#             if not qa_text:
#                 await self.send(text_data=json.dumps({
#                     "type": "error",
#                     "message": "No Foundation answers found."
#                 }))
#                 await self.close()
#                 return

#             prompt = f"""
# You are THE BRAND GODFATHER — world-class brand strategist.

# Analyze all Foundation stage questions and answers below and generate a comprehensive summary (800-1200 words).

# QUESTIONS & ANSWERS:
# {qa_text}
# """

#             system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.
# Speak in bold, direct, no-jargon tone. Reveal patterns and emotional truths.
# """

#             # Call OpenAI in streaming mode (sync client wrapped in thread)
#             stream = await sync_to_async(client.chat.completions.create)(
#                 model="gpt-4o",
#                 messages=[
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.4,
#                 max_tokens=1200,
#                 stream=True,
#             )

#             for chunk in stream:
#                 if not chunk.choices:
#                     continue

#                 delta = chunk.choices[0].delta
#                 if hasattr(delta, "content") and delta.content:
#                     await self.send(text_data=json.dumps({
#                         "type": "chunk",
#                         "content": delta.content
#                     }))

#             # Done signal
#             await self.send(text_data=json.dumps({
#                 "type": "done"
#             }))

#         except Exception as e:
#             logger.exception("WebSocket summary generation failed")
#             await self.send(text_data=json.dumps({
#                 "type": "error",
#                 "message": "AI service error"
#             }))
#             await self.close()




import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from django.conf import settings

from user_sessions.models import Session, Answer, FoundationSummary

# Azure OpenAI only (same as user_sessions.views)
from openai import AzureOpenAI
import os

def _get_azure_openai_client():
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    key = os.getenv('AZURE_OPENAI_API_KEY')
    if not endpoint or not key:
        raise ValueError("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY.")
    return AzureOpenAI(
        azure_endpoint=endpoint.rstrip('/'),
        api_key=key,
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
    )

def _get_azure_chat_deployment():
    return os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

logger = logging.getLogger(__name__)


class FoundationSummaryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get session id safely
        kwargs = self.scope.get("url_route", {}).get("kwargs", {})
        self.session_id = kwargs.get("pk")

        if not self.session_id:
            await self.close(code=4002)
            return

        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            print("❌ WS unauthenticated user:", user)
            await self.close(code=4001)
            return

        print("✅ WS authenticated user:", user)

        await self.accept()
        await self.generate_summary()

    async def disconnect(self, close_code):
        pass

    @sync_to_async
    def get_qa_text(self):
        session = get_object_or_404(Session, pk=self.session_id)

        answers = Answer.objects.filter(
            session=session,
            question__stage=1,
            question__is_active=True
        ).select_related("question").order_by("question__order")

        if not answers.exists():
            return None

        qa_text = ""
        for answer in answers:
            qa_text += f"Q: {answer.question.text.strip()}\n"
            qa_text += f"A: {answer.answer_text.strip()}\n\n"

        return qa_text

    @sync_to_async
    def get_or_create_summary_row(self, user):
        obj, _ = FoundationSummary.objects.get_or_create(
            session_id=self.session_id,
            defaults={
                "status": "processing",
                "generated_by": user
            }
        )
        obj.status = "processing"
        obj.error_message = None
        obj.save()
        return obj

    @sync_to_async
    def save_completed_summary(self, text):
        FoundationSummary.objects.filter(session_id=self.session_id).update(
            summary_text=text,
            status="completed",
            error_message=None
        )

    @sync_to_async
    def save_failed_summary(self, error_msg):
        FoundationSummary.objects.filter(session_id=self.session_id).update(
            status="failed",
            error_message=error_msg
        )

    async def generate_summary(self):
        full_text = ""

        try:
            # Mark DB row as processing
            await self.get_or_create_summary_row(self.scope["user"])

            qa_text = await self.get_qa_text()
            if not qa_text:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "No Foundation answers found."
                }))
                await self.save_failed_summary("No Foundation answers found.")
                await self.close()
                return

            prompt = f"""
You are THE BRAND GODFATHER — world-class brand strategist.

Analyze all Foundation stage questions and answers below and generate a comprehensive summary (800-1200 words).

QUESTIONS & ANSWERS:
{qa_text}
"""

            system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.
Speak in bold, direct, no-jargon tone. Reveal patterns and emotional truths.
"""

            client = _get_azure_openai_client()
            stream = await sync_to_async(client.chat.completions.create)(
                model=_get_azure_chat_deployment(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1200,
                stream=True,
            )

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_text += delta.content

                    # Send chunk to frontend
                    await self.send(text_data=json.dumps({
                        "type": "chunk",
                        "content": delta.content
                    }))

            # ✅ Save final result
            await self.save_completed_summary(full_text)

            # Done signal
            await self.send(text_data=json.dumps({
                "type": "done"
            }))

        except Exception as e:
            logger.exception("WebSocket summary generation failed")

            await self.save_failed_summary(str(e))

            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "AI service error"
            }))
            await self.close()
