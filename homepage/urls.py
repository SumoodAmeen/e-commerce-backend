"""
URL routing for Homepage module.
"""

from django.urls import path
from .views import HomepageHeroView


urlpatterns = [
    path('hero/', HomepageHeroView.as_view(), name='homepage-hero'),
]
