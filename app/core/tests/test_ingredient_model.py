# """Test ingredient model"""

# from django.test import TestCase
# from django.contrib.auth import get_user_model

# from core import models


# class IngredientTest(TestCase):
#     """Test ingredient object"""

#     def test_create_ingredient(self):
#         """Test creating ingredient object in database"""
#         user = get_user_model().objects.create_user(
#             email='test@example.com',
#             password='testpass1234'
#             )
#         ingredient = models.Ingredient.objects.create(name='Test Ingredient', user=user)

#         self.assertEqual(str(ingredient), ingredient.name)
