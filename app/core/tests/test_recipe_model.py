"""Test Recipe Model"""

from decimal import Decimal
from unittest.mock import patch


from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models


class RecipeModelTest(TestCase):
    """Test recipe object"""

    def test_create_recipe_object(self):
        """Test a Creating Recipe is successful."""

        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass1234"
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title="sample recipe name",
            description="sample recipe description",
            price=Decimal("5.89"),
            duration=10,
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
