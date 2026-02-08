"""
DRF Views for ContactInfo.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import ContactInfo
from .serializers import ContactInfoSerializer, ContactInfoCreateUpdateSerializer
from catalog.permissions import IsAdminUser


class PublicContactViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API for reading contact info.
    
    GET /api/contact/ - List active contact info
    """
    
    permission_classes = [AllowAny]
    serializer_class = ContactInfoSerializer
    
    def get_queryset(self):
        return ContactInfo.objects.filter(is_active=True).order_by('-created_at')


class AdminContactViewSet(viewsets.ModelViewSet):
    """
    Admin API for contact info CRUD.
    
    POST /api/admin/contact/ - Create
    PUT /api/admin/contact/{id}/ - Update
    DELETE /api/admin/contact/{id}/ - Delete
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = ContactInfo.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContactInfoCreateUpdateSerializer
        return ContactInfoSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'detail': 'Contact info deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )
