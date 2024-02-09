"""Test Recipe Api"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    )
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return sample recipe"""

    defaults = {
        "title": "sample recipe name",
        "description": "sample recipe description",
        "price": Decimal("5.89"),
        "duration": 20,
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call recipe API"""

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivetRecipeAPITests(TestCase):
    """Test Authenticated API requests"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass1234"
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipe limited to authenticated user"""

        other_user = get_user_model().objects.create_user(
            email="other@example.com",
            password="otherpass123",
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            "title": "test recipe title",
            "duration": 5,
            "price": Decimal("20.34"),
            "description": "test recipe description",
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_recipe_partial_update(self):
        """Test Partial update of recipe"""
        original_title = "sample recipe"
        payload = {
            "title": original_title,
            "description": "sample recipe description",
        }
        recipe = create_recipe(user=self.user, **payload)
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, original_title)
        self.assertEqual(recipe.description, payload["description"])
        self.assertEqual(recipe.user, self.user)

    def test_recipe_full_update(self):
        """Test full update of recipe"""
        payload = {
            "title": "test title",
            "description": "test description",
            "duration": 10,
            "price": Decimal("3.23"),
        }

        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error"""

        new_user = get_user_model().objects.create_user(
            email="newuser@example.com", password="testpass12345"
        )
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        payload = {"user": new_user.id}

        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting recipe successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        recipe_exists = Recipe.objects.filter(id=recipe.id)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(recipe_exists)

    def test_delete_other_user_recipe(self):
        """Test trying delete another users recipe give error"""

        new_user = get_user_model().objects.create_user(
            email="newuser@example.com", password="testpass12345"
        )

        recipe = create_recipe(new_user)
        url = detail_url(recipe.id)

        res = self.client.delete(url)
        recipe_exists = Recipe.objects.filter(id=recipe.id)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(recipe_exists)

    def test_create_new_recipe_with_tag(self):
        """Test creating a recipe with tags"""

        payload = {
            'title': 'Sample Recipe',
            'duration': 10,
            'price': 10.44,
            'description': 'Sample Recipe Description',
            'tags': [
                {'name': 'BreakFast', "user": self.user},
                {'name': 'Lunch', 'user': self.user}
                ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count, 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""

        breakfast_tag = Tag.objects.create(name='breackfast', user=self.user)

        payload = {
            'title': 'Recipe Title',
            'duration': 10,
            'price': 20,
            'description': 'Recipe Description',
            'tags': [{'name': breakfast_tag, 'user': self.user},
                     {'name': 'Lunch', 'user': self.user}
                     ]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count, 2)
        self.assertIn(breakfast_tag, recipe.tags.all())

    def test_create_tag_on_update(self):
        """"Test creating tag when updating a recipe """

        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.tags.count(), 1)

        new_tag = Tag.objects.get(name='Lunch', user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""

        recipe = create_recipe(user=self.user)
        breakfast_tag = Tag.objects.create(name='Breakfast', user=self.user)

        recipe.tags.add(breakfast_tag)

        tag_lunch = Tag.objects.create(name='Lunch', user=self.user)

        payload = {'tags': [{'name': 'lunch', 'user': self.user}]}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(breakfast_tag, recipe.tags.all())

    def test_clear_tag_recipe(self):
        """Test clear tag to recipe update"""

        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(name='Lunch', user=self.user)

        recipe.tags.add(tag)

        payload = {[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags)
        self.assertEqual(recipe.tags.count(), 0)
        
