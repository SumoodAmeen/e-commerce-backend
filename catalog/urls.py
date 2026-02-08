"""
URL routing for the Catalog API.

URL structure:
- /api/collections/              - Public: list active collections
- /api/collections/{slug}/       - Public: get collection by slug
- /api/admin/collections/        - Admin: full CRUD operations
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PublicCollectionViewSet, AdminCollectionViewSet


# Create routers
public_router = DefaultRouter()
public_router.register(r'collections', PublicCollectionViewSet, basename='public-collection')

admin_router = DefaultRouter()
admin_router.register(r'collections', AdminCollectionViewSet, basename='admin-collection')


urlpatterns = [
    # Public API endpoints
    path('', include(public_router.urls)),
    
    # Admin API endpoints (JWT protected)
    path('admin/', include(admin_router.urls)),
]
