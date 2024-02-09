"""Test Tag Model"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Tag


class TagModelTest(TestCase):
    """Test tag objects"""

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass1234"
        )

    def test_tags_create(self):
        """Test creating tag object successful"""

        preload = {"name": "Test Tag", "user": self.user}

        tag = Tag.objects.create(**preload)

        self.assertEqual(str(tag), tag.name)
