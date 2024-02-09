"""Test Recipe Model"""

from decimal import Decimal

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
