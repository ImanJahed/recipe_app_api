"""Test User model"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class TestUser(TestCase):
    """Test User model"""

    def test_create_user_with_email_successfully(self):
        """Test creating a user with an email is successfully."""

        email = "test@example.com"
        password = "testpass12345"

        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""

        sample_emails = [
            ["TEST1@EXAMPLE.COM", "TEST1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["test3@EXAMPLE.com", "test3@example.com"],
            ["test4@example.com", "test4@example.com"],
        ]

        password = "sample12345"

        for email, expected_email in sample_emails:
            user = get_user_model().objects.create_user(email=email, password=password)
            self.assertEqual(user.email, expected_email)

    def test_new_user_without_email_raises_error(self):
        """Test that crating a user without an email raises a ValueError"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="test12345")

    def test_creating_superuser(self):
        """Test creating a superuser."""

        email = "admin@example.com"
        password = "admin123456"

        user = get_user_model().objects.create_superuser(
            email=email, password=password
        )

        self.assertTrue(user.is_supperuser)
        self.assertTrue(user.is_staff)
