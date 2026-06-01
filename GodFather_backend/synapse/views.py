from celery.result import AsyncResult
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from synapse.services.orchestrator import QuestionOrchestrator
from synapse.services.question_router import QuestionRouter
from synapse.services.session_manager import SessionManager
from synapse.tasks import process_answer_async


class SynapseAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = str(request.data.get("session_id", "")).strip()
        q_id = str(request.data.get("q_id", "")).strip()
        answer = str(request.data.get("answer", "")).strip()
        use_async = bool(request.data.get("async", False))

        if not session_id or not q_id or not answer:
            return Response(
                {"detail": "session_id, q_id, and answer are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if use_async:
            task = process_answer_async.delay(session_id=session_id, q_id=q_id, user_answer=answer)
            return Response(
                {"task_id": task.id, "status": "PENDING"},
                status=status.HTTP_202_ACCEPTED,
            )

        orchestrator = QuestionOrchestrator()
        result = orchestrator.process_answer(session_id=session_id, q_id=q_id, user_answer=answer)
        payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        return Response(payload, status=status.HTTP_200_OK)


class SynapseAnswerStatusAPIView(APIView):
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


class SynapseSessionStartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = str(request.data.get("user_id", "")).strip()
        context_data = request.data.get("context_data", {}) or {}

        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        manager = SessionManager()
        router = QuestionRouter()
        session = manager.create_session(user_id=user_id, context_data=context_data)
        first = router.get_question("Q1")

        return Response(
            {
                "session_id": session.session_id,
                "first_question": {
                    "q_id": "Q1",
                    "phase": first.phase if first else "I",
                    "prompt": first.prompt if first else "",
                },
                "welcome_sequence": [
                    "Welcome to Synapse.",
                    "We will go one layer deeper on every answer.",
                    "Start with complete honesty, not polished positioning.",
                ],
            },
            status=status.HTTP_201_CREATED,
        )


class SynapseSessionDetailAPIView(APIView):
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
