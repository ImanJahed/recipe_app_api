"""Test Tag API"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core import models
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagApiTest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivetTagApiTest(TestCase):
    """Test authenticate API request"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_list_of_tags(self):
        """Test Retrieving list of tags"""

        models.Tag.objects.create(user=self.user, name='Vegan')
        models.Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = models.Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user"""

        another_user = get_user_model().objects.create(
            email='test@gmail.com',
            password='testpass123'
        )

        models.Tag.objects.create(name='Test tag1', user=another_user)
        tag = models.Tag.objects.create(name='Lunch', user=self.user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = models.Tag.objects.create(name='Breakfast', user=self.user)

        payload = {
            'name': 'Lunch'
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

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

    def test_filter_tags_assigned_to_recipe(self):
        """Test listing tags by those assigned to recipe"""

        t1 = models.Tag.objects.create(name='Tag1', user=self.user)
        t2 = models.Tag.objects.create(name='Tag2', user=self.user)

        r1 = models.Recipe.objects.create(
            title='Title for ing1',
            duration=50,
            price=Decimal('44.00'),
            description='Description for ing1',
            user=self.user
        )
        r1.tags.add(t1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(t1)
        s2 = TagSerializer(t2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
