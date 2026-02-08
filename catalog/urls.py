"""
URL routing for the Catalog API.

URL structure:
- /api/collections/              - Public: list active collections
- /api/collections/{slug}/       - Public: get collection by slug
- /api/products/                 - Public: list active products
- /api/products/{slug}/          - Public: get product by slug
- /api/admin/collections/        - Admin: collection CRUD
- /api/admin/products/           - Admin: product CRUD
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PublicCollectionViewSet,
    AdminCollectionViewSet,
    PublicProductViewSet,
    AdminProductViewSet,
)


# Create routers
public_router = DefaultRouter()
public_router.register(r'collections', PublicCollectionViewSet, basename='public-collection')
public_router.register(r'products', PublicProductViewSet, basename='public-product')

admin_router = DefaultRouter()
admin_router.register(r'collections', AdminCollectionViewSet, basename='admin-collection')
admin_router.register(r'products', AdminProductViewSet, basename='admin-product')


urlpatterns = [
    # Public API endpoints
    path('', include(public_router.urls)),
    
    # Admin API endpoints (JWT protected)
    path('admin/', include(admin_router.urls)),
]
