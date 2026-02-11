"""
DRF views for Cart & Wishlist.

Architecture:
- All endpoints require JWT authentication
- User is always inferred from request.user
- Object-level permissions prevent cross-user access (IDOR)
- No business logic lives here — delegated to serializers

Views use APIView (not ModelViewSet) for explicit, predictable routing
that matches the frontend's expected API contract.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Wishlist, WishlistItem
from .permissions import IsCartOwner, IsWishlistOwner
from .serializers import (
    AddToCartSerializer,
    AddToWishlistSerializer,
    CartItemReadSerializer,
    CartReadSerializer,
    UpdateCartItemSerializer,
    WishlistItemReadSerializer,
    WishlistReadSerializer,
)


# =========================================================================
# Cart Views
# =========================================================================

class CartView(APIView):
    """
    GET /api/cart/

    Returns the authenticated user's cart with all items,
    subtotals, and a cart total.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = Cart.objects.prefetch_related(
                'items__product',
                'items__product_size',
            ).get(user=request.user)
        except Cart.DoesNotExist:
            # Return an empty cart structure (not a 404)
            return Response({
                'id': None,
                'items': [],
                'cart_total': '0.00',
                'item_count': 0,
                'updated_at': None,
            })

        serializer = CartReadSerializer(cart, context={'request': request})
        return Response(serializer.data)


class AddToCartView(APIView):
    """
    POST /api/cart/add/

    Accepts: { product_id, size_id, quantity }
    - Creates cart if it doesn't exist
    - Increments quantity if product+size already in cart
    - Validates stock server-side
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()

        read_serializer = CartItemReadSerializer(
            cart_item, context={'request': request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """
    PUT  /api/cart/item/{id}/  — update quantity
    DELETE /api/cart/item/{id}/  — remove item
    """

    permission_classes = [IsAuthenticated, IsCartOwner]

    def get_object(self, pk, user):
        """
        Fetch the cart item or return None.

        Filters by user's cart to prevent IDOR regardless of the
        permission class (defense in depth).
        """
        try:
            cart_item = (
                CartItem.objects
                .select_related('cart', 'product', 'product_size')
                .get(pk=pk, cart__user=user)
            )
        except CartItem.DoesNotExist:
            return None

        # Run object-level permission check
        self.check_object_permissions(self.request, cart_item)
        return cart_item

    def put(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        if cart_item is None:
            return Response(
                {'detail': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={'request': request, 'cart_item': cart_item},
        )
        serializer.is_valid(raise_exception=True)

        cart_item.quantity = serializer.validated_data['quantity']
        cart_item.save(update_fields=['quantity', 'updated_at'])

        read_serializer = CartItemReadSerializer(
            cart_item, context={'request': request},
        )
        return Response(read_serializer.data)

    def delete(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        if cart_item is None:
            return Response(
                {'detail': 'Cart item not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================================================================
# Wishlist Views
# =========================================================================

class WishlistView(APIView):
    """
    GET /api/wishlist/

    Returns the authenticated user's wishlist.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wishlist = Wishlist.objects.prefetch_related(
                'items__product',
            ).get(user=request.user)
        except Wishlist.DoesNotExist:
            return Response({
                'id': None,
                'items': [],
                'item_count': 0,
                'updated_at': None,
            })

        serializer = WishlistReadSerializer(
            wishlist, context={'request': request},
        )
        return Response(serializer.data)


class AddToWishlistView(APIView):
    """
    POST /api/wishlist/add/

    Accepts: { product_id }
    - Creates wishlist if it doesn't exist
    - Prevents duplicate products
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToWishlistSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        wishlist_item = serializer.save()

        read_serializer = WishlistItemReadSerializer(
            wishlist_item, context={'request': request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class WishlistItemDetailView(APIView):
    """
    DELETE /api/wishlist/item/{id}/  — remove item
    """

    permission_classes = [IsAuthenticated, IsWishlistOwner]

    def get_object(self, pk, user):
        """
        Fetch the wishlist item scoped to the user's wishlist.
        Defense in depth: filters by user even before permission check.
        """
        try:
            wishlist_item = (
                WishlistItem.objects
                .select_related('wishlist', 'product')
                .get(pk=pk, wishlist__user=user)
            )
        except WishlistItem.DoesNotExist:
            return None

        self.check_object_permissions(self.request, wishlist_item)
        return wishlist_item

    def delete(self, request, pk):
        wishlist_item = self.get_object(pk, request.user)
        if wishlist_item is None:
            return Response(
                {'detail': 'Wishlist item not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
