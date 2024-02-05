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

    def test_create_user_success(self):
        """Test creating a user successfully"""
        payload = {
            "email": "test@example.com",
            "password": "testpass1234",
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_with_emil_exists_error(self):
        """Test error returned if user with email exists"""
        payload = {
            "email": "test@example.com",
            "password": "testpass1234",
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_password_short_error(self):
        """Test an error is returned if password less than 5 chars"""
        payload = {"email": "test@example.com", "password": "123"}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        user_detail = {
            "email": "test@example.com",
            "password": "testpass1234",
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
        }
        create_user(**user_detail)
        payload = {
            'email': user_detail["email"],
            'password': user_detail["password"]
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credential(self):
        """Test returned error for invalid credential"""
        create_user(email='test@example', password='testpass1234')

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
        self.client = APIClient()

        self.payload = {
            "email": "test@example.com",
            "password": "testpass1234",
            "first_name": "Test First Name",
            "last_name": "Test Last Name",
        }
        self.user = create_user(**self.payload)
        self.client.force_authenticate(self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
        )

    def test_post_method_not_allowed_me_endpoint(self):
        """Test Not allowed post request to me endpoint"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating profile from authenticated user"""

        payload = {
            "first_name": "New First Name",
            "last_name": "New Last Name",
            "password": "newpass12345",
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, payload["first_name"])
        self.assertTrue(self.user.check_password(payload["password"]))
