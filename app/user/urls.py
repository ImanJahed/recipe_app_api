"""Url mapping for user API."""

from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('create/', views.UserAPIView.as_view(), name='create'),
    path('token/', views.AuthTokenView.as_view(), name='token'),
    path('me/', views.UserManagerAPI.as_view(), name='me')

]
