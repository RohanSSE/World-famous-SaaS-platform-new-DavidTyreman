from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role
from accounts.models import User
from user_sessions.models import Answer
from user_sessions.models import Question
from user_sessions.models import Session


class SessionAnswerPermissionTests(TestCase):
    def setUp(self):
        self.client_role = Role.objects.create(name="client", is_active=True)
        self.owner = User.objects.create_user(email="owner@example.com", password="pass12345")
        self.owner.role = self.client_role
        self.owner.save(update_fields=["role"])
        self.other_user = User.objects.create_user(email="other@example.com", password="pass12345")
        self.other_user.role = self.client_role
        self.other_user.save(update_fields=["role"])
        self.session = Session.objects.create(
            title="Owner session",
            created_by=self.owner,
            status="draft",
        )
        self.question = Question.objects.create(
            text="Why did you start this business?",
            category="brand_identity",
            stage=1,
            order=1,
            is_required=True,
            is_active=True,
        )
        self.api_client = APIClient()

    def test_owner_can_list_answers_without_answer_role_permission(self):
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.get(f"/api/sessions/{self.session.id}/answers/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_owner_can_create_answer_without_answer_role_permission(self):
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.post(
            f"/api/sessions/{self.session.id}/answers/create/",
            {
                "question": self.question.id,
                "answer_text": "I wanted to create meaningful change.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Answer.objects.count(), 1)
        answer = Answer.objects.get()
        self.assertEqual(answer.session, self.session)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.answered_by, self.owner)

    def test_non_owner_still_cannot_access_session_answers(self):
        self.api_client.force_authenticate(user=self.other_user)

        response = self.api_client.get(f"/api/sessions/{self.session.id}/answers/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Access denied")
