from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from .models import Agency, Role, User
from .views import login_with_email, register


class AgencyLoginTests(APITestCase):
    password = "AgencyPass123!"

    def setUp(self):
        self.factory = APIRequestFactory()

    def post_to_view(self, view, data):
        request = self.factory.post("/", data, format="json")
        return view(request)

    def test_pending_agency_login_returns_pending_approval(self):
        response = self.post_to_view(
            register,
            {
                "email": "pending-agency@example.com",
                "password": self.password,
                "confirm_password": self.password,
                "user_type": "agency",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["pending_approval"])

        login_response = self.post_to_view(
            login_with_email,
            {"email": "pending-agency@example.com", "password": self.password},
        )

        self.assertEqual(login_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(login_response.data["code"], "agency_pending_approval")

    def test_approved_agency_can_login(self):
        role, _ = Role.objects.get_or_create(name="agency", defaults={"description": "Role: agency"})
        user = User.objects.create_user(
            email="approved-agency@example.com",
            password=self.password,
            is_active=True,
        )
        user.role = role
        user.save(update_fields=["role"])
        agency = Agency.objects.create(
            name="Approved Agency",
            owner=user,
            is_active=True,
            approved_at=timezone.now(),
        )
        user.agency = agency
        user.save(update_fields=["agency"])

        response = self.post_to_view(
            login_with_email,
            {"email": "approved-agency@example.com", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role_name"], "agency")

    def test_login_repairs_agency_approved_without_synced_owner(self):
        role, _ = Role.objects.get_or_create(name="agency", defaults={"description": "Role: agency"})
        user = User.objects.create_user(
            email="stale-approved-agency@example.com",
            password=self.password,
            is_active=False,
        )
        user.role = role
        user.save(update_fields=["role"])
        agency = Agency.objects.create(
            name="Stale Approved Agency",
            owner=user,
            is_active=True,
            approved_at=None,
        )
        user.agency = agency
        user.save(update_fields=["agency"])

        response = self.post_to_view(
            login_with_email,
            {"email": "stale-approved-agency@example.com", "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        agency.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(agency.approved_at)

    def test_wrong_password_still_returns_invalid_credentials(self):
        role, _ = Role.objects.get_or_create(name="agency", defaults={"description": "Role: agency"})
        user = User.objects.create_user(
            email="wrong-password-agency@example.com",
            password=self.password,
            is_active=False,
        )
        user.role = role
        user.save(update_fields=["role"])

        response = self.post_to_view(
            login_with_email,
            {"email": "wrong-password-agency@example.com", "password": "WrongPass123!"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid email or password")
