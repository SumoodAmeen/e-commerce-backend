"""
URL routing for Contact module.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PublicContactViewSet, AdminContactViewSet


# Create routers
public_router = DefaultRouter()
public_router.register(r'', PublicContactViewSet, basename='public-contact')

admin_router = DefaultRouter()
admin_router.register(r'', AdminContactViewSet, basename='admin-contact')


urlpatterns = [
    # Public API
    path('', include(public_router.urls)),
    
    # Admin API (JWT protected)
    path('admin/', include(admin_router.urls)),
]
