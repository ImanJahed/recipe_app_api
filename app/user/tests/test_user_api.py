"""Test User API"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """Test the public features of the user api"""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "email": "test@example.com",
            "password": "testpass1234",
            "name": "Test Name",
        }
        self.user = create_user(**self.payload)

    def test_create_user_success(self):
        """Test creating a user successfully"""

        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_emil_exists_error(self):
        """Test error returned if user with email exists"""

        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_password_short_error(self):
        """Test an error is returned if password less than 5 chars"""

        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=self.payload["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):

        res = self.client.post(TOKEN_URL, self.payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credential(self):
        """Test returned error for invalid credential"""

        payload = {
            "email": "",
            "password": "badpass",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_create_token_for_blank_password(self):
        """Test returned error for posting a user blank password"""

        payload = {"email": "test@example.com", "password": ""}

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", res.data)

    def test_retrieve_user_unauthorize(self):
        """Test authentication required for user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Test API requests that required authentication."""

    def setUp(self):
        self.payload = {
            "email": "test@example.com",
            "password": "testpass1234",
            "name": "Test Name",
        }
        self.user = create_user(**self.payload)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data, {"email": self.user["email"], "name": self.user["name"]}
        )

    def test_post_method_not_allowed_me_endpoint(self):
        """Test Not allowed post request to me endpoint"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating profile from authenticated user"""

        self.payload = {
            "name": "New Name",
            "password": "newpass12345",
        }

        res = self.client.patch(ME_URL, self.payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, self.payload["name"])
        self.assertTrue(self.user.check_password(self.payload["password"]))
