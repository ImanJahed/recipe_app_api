"""Test Ingredient APIs"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe
from recipe import serializers


INGREDIENT_URLS = reverse("recipe:ingredient-list")


def create_user(email="test@example.com", password="testpass123"):
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(ingredient_id):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


class PublicIngredientApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_get_error(self):
        """Test retrieve error for unauthenticated user"""
        user = create_user()
        Ingredient.objects.create(name="Test Ingredient", user=user)

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()

        self.client.force_authenticate(self.user)

    def test_auth_required(self):
        """Test retrieve list of ingredient"""

        Ingredient.objects.create(name="Ingredient1", user=self.user)
        Ingredient.objects.create(name="Ingredient2", user=self.user)

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = serializers.IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(ingredients.count(), 2)
        ingredient = ingredients[0]
        self.assertEqual(ingredient.name, "Ingredient2")

    def test_ingredient_limited_to_user(self):
        """Test list of ingredient is limited to authenticated user"""

        user2 = create_user(email="test2@example.com", password="testpass1234")

        Ingredient.objects.create(name="Ingredient user2", user=user2)
        ingredient = Ingredient.objects.create(name="Test Ingredient", user=self.user)

        res = self.client.get(INGREDIENT_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test update ingredient"""

        ingredient = Ingredient.objects.create(name="Ingredient", user=self.user)
        payload = {"name": "Ingredient Updated"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test delete ingredient"""

        ingredient = Ingredient.objects.create(name="Ingredient test", user=self.user)

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        exists_ingredient = Ingredient.objects.filter(user=self.user).exists()
        self.assertFalse(exists_ingredient)

    def test_filter_ingredients_assigned_to_recipe(self):
        """Test listing ingredient by those assigned to recipe"""

        ing1 = Ingredient.objects.create(name='Ingredient1', user=self.user)
        ing2 = Ingredient.objects.create(name='Ingredient1', user=self.user)

        r1 = Recipe.objects.create(
            title='Title for ing1',
            duration=50,
            price=Decimal('44.00'),
            description='Description for ing1',
            user=self.user
        )

        r1.ingredients.add(ing1)

        res = self.client.get(INGREDIENT_URLS, {'assigned_only': 1})

        s1 = serializers.IngredientSerializer(ing1)
        s2 = serializers.IngredientSerializer(ing2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)
