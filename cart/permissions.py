"""
Object-level permission classes for Cart & Wishlist.

These prevent IDOR attacks by ensuring a user can only access
their own cart items and wishlist items.
"""

from rest_framework import permissions


class IsCartOwner(permissions.BasePermission):
    """
    Object-level check: the cart item must belong to the requesting user.
    """

    def has_object_permission(self, request, view, obj):
        return obj.cart.user == request.user


class IsWishlistOwner(permissions.BasePermission):
    """
    Object-level check: the wishlist item must belong to the requesting user.
    """

    def has_object_permission(self, request, view, obj):
        return obj.wishlist.user == request.user
