"""
DRF Views for the Collection API.

Architecture:
- PublicCollectionViewSet: Read-only access for frontend (no auth required)
- AdminCollectionViewSet: Full CRUD for admin users (JWT required)

Security:
- Strict permission classes
- Clean separation of public vs admin endpoints
- No sensitive data in error responses
"""

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Collection
from .serializers import (
    CollectionListSerializer,
    CollectionDetailSerializer,
    CollectionCreateSerializer,
    CollectionUpdateSerializer,
    CollectionAdminSerializer,
)
from .permissions import IsAdminUser


class PublicCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for collection listing.
    
    This viewset provides read-only access to active collections
    for the frontend. No authentication required.
    
    Endpoints:
    - GET /api/collections/ - List all active collections
    - GET /api/collections/{slug}/ - Get collection detail by slug
    """
    
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return only active collections for public access.
        Ordered by creation date (newest first).
        """
        return Collection.objects.filter(is_active=True).order_by('-created_at')
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return CollectionListSerializer
        return CollectionDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List active collections.
        
        Optimized query for frontend listing.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get single collection by slug.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AdminCollectionViewSet(viewsets.ModelViewSet):
    """
    Admin API for collection management.
    
    This viewset provides full CRUD access to collections
    for authenticated admin/staff users.
    
    Endpoints:
    - GET /api/admin/collections/ - List all collections
    - POST /api/admin/collections/ - Create new collection
    - GET /api/admin/collections/{id}/ - Get collection detail
    - PUT /api/admin/collections/{id}/ - Update collection
    - PATCH /api/admin/collections/{id}/ - Partial update
    - DELETE /api/admin/collections/{id}/ - Delete collection
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Collection.objects.all().order_by('-created_at')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'is_active']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return CollectionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CollectionUpdateSerializer
        elif self.action == 'list':
            return CollectionAdminSerializer
        return CollectionDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List all collections for admin view.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new collection.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing collection.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a collection.
        
        Also deletes the associated image file to prevent orphaned files.
        """
        instance = self.get_object()
        
        # Delete image file if exists
        if instance.image:
            instance.image.delete(save=False)
        
        self.perform_destroy(instance)
        
        return Response(
            {'detail': 'Collection deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a collection.
        """
        instance = self.get_object()
        instance.is_active = True
        instance.save(update_fields=['is_active', 'updated_at'])
        
        serializer = CollectionDetailSerializer(instance, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a collection.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        
        serializer = CollectionDetailSerializer(instance, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """
        Bulk activate multiple collections.
        
        Request body: {"ids": [1, 2, 3]}
        """
        ids = request.data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return Response(
                {'detail': 'Please provide a list of collection IDs.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter to only valid IDs that the user can access
        updated_count = Collection.objects.filter(pk__in=ids).update(is_active=True)
        
        return Response({
            'detail': f'{updated_count} collection(s) activated successfully.'
        })
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """
        Bulk deactivate multiple collections.
        
        Request body: {"ids": [1, 2, 3]}
        """
        ids = request.data.get('ids', [])
        
        if not ids or not isinstance(ids, list):
            return Response(
                {'detail': 'Please provide a list of collection IDs.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter to only valid IDs
        updated_count = Collection.objects.filter(pk__in=ids).update(is_active=False)
        
        return Response({
            'detail': f'{updated_count} collection(s) deactivated successfully.'
        })
