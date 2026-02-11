"""
URL routing for Cart & Wishlist APIs.

All endpoints require JWT authentication.
"""

from django.urls import path

from .views import (
    AddToCartView,
    AddToWishlistView,
    CartItemDetailView,
    CartView,
    WishlistItemDetailView,
    WishlistView,
)

urlpatterns = [
    # ── Cart ──────────────────────────────────────────────────
    path('cart/', CartView.as_view(), name='cart-detail'),
    path('cart/add/', AddToCartView.as_view(), name='cart-add'),
    path('cart/item/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),

    # ── Wishlist ──────────────────────────────────────────────
    path('wishlist/', WishlistView.as_view(), name='wishlist-detail'),
    path('wishlist/add/', AddToWishlistView.as_view(), name='wishlist-add'),
    path('wishlist/item/<int:pk>/', WishlistItemDetailView.as_view(), name='wishlist-item-detail'),
]
