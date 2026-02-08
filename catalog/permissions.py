"""
Custom permission classes for the catalog API.

Security principle: Default deny - explicitly grant access.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Read access (GET, HEAD, OPTIONS) to everyone
    - Write access (POST, PUT, PATCH, DELETE) only to admin users
    
    Used for public collection listing endpoints.
    """
    
    def has_permission(self, request, view):
        # Allow read-only methods for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions require admin/staff status
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission that only allows admin/staff users.
    
    Used for admin-only endpoints like collection create/update/delete.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Read access to everyone
    - Write access only to authenticated users
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated


class HasCollectionPermission(permissions.BasePermission):
    """
    Object-level permission for collection operations.
    
    Ensures users can only modify collections they have explicit permission for.
    This is useful when implementing dealer/vendor-specific collections.
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Staff always has permission
        if request.user.is_staff:
            return True
        
        # Check for specific collection permissions
        return request.user.has_perm('catalog.change_collection')
    
    def has_object_permission(self, request, view, obj):
        # Staff can modify any collection
        if request.user.is_staff:
            return True
        
        # For non-staff, check object-level permissions
        # This can be extended to check ownership, vendor relationship, etc.
        return request.user.has_perm('catalog.change_collection')
