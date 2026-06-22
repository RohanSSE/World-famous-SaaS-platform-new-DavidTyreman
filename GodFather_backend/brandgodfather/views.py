from celery.result import AsyncResult
from elasticsearch_dsl import connections
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from brandgodfather.services.orchestrator import QuestionOrchestrator
from brandgodfather.services.question_router import QuestionRouter
from brandgodfather.services.ragv2.discovery_metadata import build_discovery_metadata
from brandgodfather.services.session_manager import SessionManager
from brandgodfather.tasks import process_answer_async


class BrandGodFatherAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = str(request.data.get("session_id", "")).strip()
        q_id = str(request.data.get("q_id", "")).strip()
        answer = str(request.data.get("answer", "")).strip()
        context_data = request.data.get("context_data", {}) or {}
        use_async = bool(request.data.get("async", False))

        if not session_id or not q_id or not answer:
            return Response(
                {"detail": "session_id, q_id, and answer are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if use_async:
            task = process_answer_async.delay(session_id=session_id, q_id=q_id, user_answer=answer)
            discovery_metadata = build_discovery_metadata(session_id=session_id, q_id=q_id, raw_answer=answer)
            return Response(
                {"task_id": task.id, "status": "PENDING", "discovery_metadata": discovery_metadata},
                status=status.HTTP_202_ACCEPTED,
            )

        manager = SessionManager()
        if isinstance(context_data, dict) and context_data:
            existing = manager.get_session(session_id)
            existing_context = existing.context_data if existing else {}
            merged_context = {**(existing_context or {}), **context_data}
            if existing:
                manager.update_session(session_id, {"context_data": merged_context})

        try:
            orchestrator = QuestionOrchestrator()
        except Exception as exc:
            return Response(
                {"detail": f"BrandGodFather ORB engine unavailable: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            result = orchestrator.process_answer(session_id=session_id, q_id=q_id, user_answer=answer)
        except ValueError as exc:
            if "Session not found" not in str(exc):
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

            user_id = str(getattr(request.user, "id", "") or getattr(request.user, "email", "") or "frontend-user")
            manager.ensure_session(
                session_id=session_id,
                user_id=user_id,
                context_data={
                    **(context_data if isinstance(context_data, dict) else {}),
                    "recovered_from_answer_request": True,
                    "source": "brandgodfather_answer_api",
                },
            )
            try:
                result = orchestrator.process_answer(session_id=session_id, q_id=q_id, user_answer=answer)
            except Exception as retry_exc:
                return Response(
                    {"detail": f"BrandGodFather ORB session recovery failed: {retry_exc}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        except Exception as exc:
            return Response(
                {"detail": f"BrandGodFather ORB answer failed: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        payload["discovery_metadata"] = build_discovery_metadata(session_id=session_id, q_id=q_id, raw_answer=answer)
        return Response(payload, status=status.HTTP_200_OK)


class BrandGodFatherAnswerStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id: str):
        task_result = AsyncResult(task_id)

        if task_result.state in ("PENDING", "STARTED", "RETRY"):
            return Response(
                {
                    "task_id": task_id,
                    "status": task_result.state,
                },
                status=status.HTTP_200_OK,
            )

        if task_result.state == "SUCCESS":
            return Response(
                {
                    "task_id": task_id,
                    "status": "SUCCESS",
                    "result": task_result.result,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(task_result.result),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class BrandGodFatherSessionStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = str(request.data.get("user_id", "")).strip()
        context_data = request.data.get("context_data", {}) or {}

        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        manager = SessionManager()
        router = QuestionRouter()
        session, reused = manager.start_or_get_session(user_id=user_id, context_data=context_data)
        first = router.get_question("Q1")
        current_q_id = session.current_q_id or "Q1"
        current = router.get_question(current_q_id)
        source_session_id = (session.context_data or {}).get("source_session_id")
        source_session_ref = (session.context_data or {}).get("source_session_ref")

        return Response(
            {
                "session_id": session.session_id,
                "source_session_id": source_session_id,
                "source_session_ref": source_session_ref,
                "reused": reused,
                "current_q_id": current_q_id,
                "current_question": {
                    "q_id": current_q_id,
                    "phase": current.phase if current else "I",
                    "prompt": current.prompt if current else "",
                },
                "first_question": {
                    "q_id": "Q1",
                    "phase": first.phase if first else "I",
                    "prompt": first.prompt if first else "",
                },
                "welcome_sequence": [
                    "Welcome to BrandGodFather.",
                    "We will go one layer deeper on every answer.",
                    "Start with complete honesty, not polished positioning.",
                ],
            },
            status=status.HTTP_201_CREATED,
        )


class BrandGodFatherSessionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: str):
        manager = SessionManager()
        router = QuestionRouter()

        session = manager.get_session(session_id)
        if session is None:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        current_q_id = session.current_q_id
        current_question = router.get_question(current_q_id)
        depth_history = manager.get_depth_history(session_id)

        payload = session.model_dump() if hasattr(session, "model_dump") else dict(session)
        payload["current_question"] = {
            "q_id": current_q_id,
            "phase": current_question.phase if current_question else "I",
            "prompt": current_question.prompt if current_question else "",
            "enforcement_rule": current_question.enforcement_rule if current_question else "",
        }
        payload["depth_history"] = depth_history
        return Response(payload, status=status.HTTP_200_OK)


class _BrandGodFatherOutputBaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    content_type = ""

    def get(self, request, session_id: str):
        es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        body = {
            "size": 1,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"session_id": session_id}},
                        {"term": {"content_type": self.content_type}},
                    ]
                }
            },
            "sort": [{"created_at": {"order": "desc", "unmapped_type": "date"}}],
        }
        resp = es.search(index="brandgodfather_output_content", body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return Response({"detail": "Output not found for this session."}, status=status.HTTP_404_NOT_FOUND)

        src = hits[0].get("_source", {})
        return Response(
            {
                "session_id": session_id,
                "content_type": self.content_type,
                "content": src.get("content"),
                "week_number": src.get("week_number"),
                "brand_filter_result": src.get("brand_filter_result", {}),
                "created_at": src.get("created_at"),
            },
            status=status.HTTP_200_OK,
        )


class BrandGodFatherOutputSocialAPIView(_BrandGodFatherOutputBaseAPIView):
    content_type = "social"


class BrandGodFatherOutputCampaignAPIView(_BrandGodFatherOutputBaseAPIView):
    content_type = "campaign"


class BrandGodFatherOutputOutreachAPIView(_BrandGodFatherOutputBaseAPIView):
    content_type = "outreach"
