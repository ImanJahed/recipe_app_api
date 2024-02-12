"""Test Recipe Api"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeDetailSerializer, RecipeSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

        recipes = Recipe.objects.all().order_by("-id")
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
            "title": "Sample Recipe",
            "duration": 10,
            "price": Decimal("10.44"),
            "description": "Sample Recipe Description",
            "tags": [{"name": "BreakFast"}, {"name": "Lunch"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""

        breakfast_tag = Tag.objects.create(name="breakfast", user=self.user)

        payload = {
            "title": "Recipe Title",
            "duration": 10,
            "price": Decimal("20.22"),
            "description": "Recipe Description",
            "tags": [{"name": "breakfast"}, {"name": "Lunch"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(breakfast_tag, recipe.tags.all())

        for tag in payload["tags"]:
            tag_exists = Tag.objects.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(tag_exists)

    def test_create_tag_on_update(self):
        """ "Test creating tag when updating a recipe"""

        recipe = create_recipe(user=self.user)
        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(name="Lunch", user=self.user)

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""

        recipe = create_recipe(user=self.user)
        breakfast_tag = Tag.objects.create(name="Breakfast", user=self.user)

        recipe.tags.add(breakfast_tag)

        tag_lunch = Tag.objects.create(name="Lunch", user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(breakfast_tag, recipe.tags.all())

    def test_clear_tag_recipe(self):
        """Test clear tag to recipe update"""

        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(name="Lunch", user=self.user)

        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags.all())
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredient(self):
        """Test creating a recipe with new ingredient"""

        payload = {
            "title": "Test title",
            "duration": 10,
            "price": Decimal("22.22"),
            "description": "Test descriptin",
            "ingredients": [{"name": "Test Ingredient1"}, {"name": "Test Ingredient2"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.all()

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            ingredient_exists = Ingredient.objects.filter(
                name=ingredient["name"], user=self.user
            )
            self.assertTrue(ingredient_exists)

    def test_create_recipe_assign_exists_ingredient(self):
        """Test creating a recipe with existing ingredient"""

        ingredient_tst = Ingredient.objects.create(name="Test name", user=self.user)
        payload = {
            "title": "Test title",
            "duration": 10,
            "price": Decimal("21.21"),
            "description": "Test description",
            "ingredients": [{"name": "Test name"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.all()
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient_tst, recipe.ingredients.all())

    def test_create_ingredient_when_update_recipe(self):
        """Test creating ingredient when update recipe"""
        recipe = create_recipe(user=self.user)
        payload = {"ingredients": [{"name": "ingredient1"}, {"name": "ingredient2"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            ingredient_exists = Ingredient.objects.filter(
                name=ingredient['name'], user=self.user).exists()
            self.assertTrue(ingredient_exists)

    def test_update_recipe_assign_exists_ingredient(self):
        """Test update recipe with existing ingredient"""

        ingredient_1 = Ingredient.objects.create(name="test name", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_1)

        ingredient_2 = Ingredient.objects.create(
            name="another ingredient", user=self.user
        )

        payload = {"ingredients": [{"name": "another ingredient"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 1)
        self.assertIn(ingredient_2, recipe.ingredients.all())
        self.assertNotIn(ingredient_1, recipe.ingredients.all())

    def test_clear_ingredient_in_recipe(self):
        """Test clear ingredient at recipe"""

        ingredient = Ingredient.objects.create(name="test name", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEqual(recipe.ingredients.count(), 0)
        self.assertNotIn(ingredient, recipe.ingredients.all())

    def test_filter_by_tags(self):
        """Test filtering a recipe by tag."""
        tag1 = Tag.objects.create(name='tag1', user=self.user)
        tag2 = Tag.objects.create(name='tag2', user=self.user)

        r1 = create_recipe(user=self.user, title='title for tag1')
        r2 = create_recipe(user=self.user, title='title for tag2')
        r3 = create_recipe(user=self.user, title='Test title')

        r1.tags.add(tag1)
        r2.tags.add(tag2)

        params = {
            'tags': f'{tag1.id}, {tag2.id}'
        }
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipe by ingredient"""

        ing1 = Ingredient.objects.create(user=self.user, name='ingredient1')
        ing2 = Ingredient.objects.create(user=self.user, name='ingredient2')

        r1 = create_recipe(user=self.user, title='title for ing1')
        r2 = create_recipe(user=self.user, title='title for ing2')
        r3 = create_recipe(user=self.user, title='Test title')

        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)
        
        params = {'ingredients': f'{ing1.id}, {ing2.id}'}

        res = self.client.get(RECIPES_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class RecipeImageTest(TestCase):
    """Test fro image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpassword1234'
        )

        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to recipe"""

        url = image_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                'image': image_file
            }

            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an image invalid image."""

        url = image_url(self.recipe.id)
        payload = {'image': 'nothing image'}

        res = self.client.post(url, payload, foramt='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
