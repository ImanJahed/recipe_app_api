"""Test Tag API"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core import models
from serializers import TagSerializer

TAGS_URL = 'recipe:tag-list'


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivetTagApiTest(TestCase):
    """Test authenticate API request"""

    def setUP(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_list_of_tags(self):
        """Test Retrieving list of tags"""

        payload = {
            'name': 'Test Tag1',
            'user': self.user
        }
        payload2 = {
            'name': 'Test Tag2',
            'user': self.user
        }
        models.Tag.objects.create(**payload)
        models.Tag.objects.create(**payload2)

        tags = models.Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""

        another_user = get_user_model(
            email='test@gmail.com',
            password='testpass123'
        )

        models.Tag.objects.create(name='Test tag1', user=another_user)
        tag = models.Tag.objects.create(name='Lunch', user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertNotIn(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = models.Tag.objects.create(name='Breakfast', user=self.user)

        payload = {
            'name': 'Lunch'
        }

        res = self.client.patch(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()

        self.assertEqual(tag.name, payload['name'])

    def test_delete_ta(self):
        """Test deleting a tag"""

        tag = models.Tag.objects.create(name='Salt', user=self.user)

        url = detail_url(tag.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags_exists = models.Tag.objects.filter(user=self.user).exists()

        self.assertFalse(tags_exists)
