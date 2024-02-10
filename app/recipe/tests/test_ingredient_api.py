"""Test Ingredient APIs"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient
from recipe import serializers


INGREDIENT_URLS = reverse('recipe:ingredient-list')


def create_user(email='test@example.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


class PublicIngredientApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_get_error(self):
        """Test retrieve error for unauthenticated user"""
        user = create_user()
        Ingredient.objects.create(name='Test Ingredient', user=user)

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()

        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient(self):
        """Test retrieve list of ingredient"""

        Ingredient.objects.create(name='Ingredient1', user=self.user)
        Ingredient.objects.create(name='Ingredient2', user=self.user)

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = Ingredient.objects.all()
        serializer = serializers.IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(ingredients.count(), 2)
        ingredient = ingredients[0]
        self.assertEqual(ingredient.name, 'Ingredient1')

    def test_retrieve_limited_ingredient(self):
        """Test retrieve ingredient for authenticated user"""

        user2 = create_user(email='test2@example.com', password='testpass1234')

        Ingredient.objects.create(name='Ingredient user2', user=user2)
        ingredient = Ingredient.objects.create(name='Test Ingredient', user=self.user)

        res = self.client.get(INGREDIENT_URLS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = serializers.IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(ingredients.count(), 1)
        ingredient = ingredients[0]
        self.assertEqual(ingredient.name, "Test Ingredient")
