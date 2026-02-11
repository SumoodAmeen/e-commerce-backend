"""
DRF serializers for Cart & Wishlist.

Design principles:
- Separate read vs write serializers
- User is ALWAYS inferred from request.user (never from body)
- All validation happens here as a second defense layer (models are first)
- Stock checks are server-side — never trust frontend quantities
"""

from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.models import Product, ProductSize
from .models import Cart, CartItem, Wishlist, WishlistItem


# =========================================================================
# Cart — Read Serializers
# =========================================================================

class CartItemReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for a single cart line-item.

    Includes product info, selected size, price, and computed subtotal.
    """

    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    price = serializers.DecimalField(
        source='product.price', max_digits=10, decimal_places=2, read_only=True,
    )
    size = serializers.CharField(source='product_size.size', read_only=True)
    size_id = serializers.IntegerField(source='product_size.id', read_only=True)
    available_stock = serializers.IntegerField(
        source='product_size.quantity', read_only=True,
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product_id',
            'product_name',
            'product_slug',
            'product_image',
            'price',
            'size',
            'size_id',
            'quantity',
            'available_stock',
            'subtotal',
            'added_at',
        ]
        read_only_fields = fields

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.main_image and request:
            return request.build_absolute_uri(obj.product.main_image.url)
        elif obj.product.main_image:
            return obj.product.main_image.url
        return None

    def get_subtotal(self, obj):
        return str(obj.subtotal)


class CartReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the entire cart.

    Includes all items and a computed cart total.
    """

    items = CartItemReadSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'cart_total', 'item_count', 'updated_at']
        read_only_fields = fields

    def get_cart_total(self, obj):
        return str(obj.total)

    def get_item_count(self, obj):
        return obj.items.count()


# =========================================================================
# Cart — Write Serializers
# =========================================================================

class AddToCartSerializer(serializers.Serializer):
    """
    Validates input for adding a product to the cart.

    Accepts product_id, size_id, quantity.  The user is inferred from
    request.user — never accepted from the request body.

    If the same product + size already exists in the cart, the quantity
    is incremented (not duplicated).
    """

    product_id = serializers.IntegerField()
    size_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_product_id(self, value):
        """Ensure the product exists and is active."""
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        if not product.is_active:
            raise serializers.ValidationError("This product is currently unavailable.")

        return value

    def validate_size_id(self, value):
        """Basic existence check — cross-field check happens in validate()."""
        if not ProductSize.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Size not found.")
        return value

    def validate(self, data):
        """
        Cross-field validation:
        - Size must belong to the specified product
        - Requested quantity must not exceed available stock
        """
        try:
            product = Product.objects.get(pk=data['product_id'])
            product_size = ProductSize.objects.get(pk=data['size_id'])
        except (Product.DoesNotExist, ProductSize.DoesNotExist):
            raise serializers.ValidationError("Invalid product or size.")

        if product_size.product_id != product.id:
            raise serializers.ValidationError({
                'size_id': "This size does not belong to the selected product."
            })

        # Calculate total quantity (existing in cart + requested)
        user = self.context['request'].user
        existing_qty = 0
        try:
            cart = Cart.objects.get(user=user)
            cart_item = CartItem.objects.get(
                cart=cart, product=product, product_size=product_size,
            )
            existing_qty = cart_item.quantity
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass

        total_qty = existing_qty + data['quantity']
        if total_qty > product_size.quantity:
            raise serializers.ValidationError({
                'quantity': (
                    f"Insufficient stock. Available: {product_size.quantity}, "
                    f"already in cart: {existing_qty}."
                )
            })

        data['_product'] = product
        data['_product_size'] = product_size
        return data

    def create(self, validated_data):
        """
        Create or increment a cart item.

        Uses select_for_update() inside a transaction for atomicity.
        """
        user = self.context['request'].user
        product = validated_data['_product']
        product_size = validated_data['_product_size']
        quantity = validated_data['quantity']

        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=user)

            # Lock the row if it exists to prevent race conditions
            cart_item = (
                CartItem.objects
                .select_for_update()
                .filter(cart=cart, product=product, product_size=product_size)
                .first()
            )

            if cart_item:
                cart_item.quantity = F('quantity') + quantity
                cart_item.save(update_fields=['quantity', 'updated_at'])
                cart_item.refresh_from_db()
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    product_size=product_size,
                    quantity=quantity,
                )

        return cart_item


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Validates quantity updates for an existing cart item.
    """

    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        """Ensure new quantity does not exceed available stock."""
        cart_item = self.context.get('cart_item')
        if cart_item and value > cart_item.product_size.quantity:
            raise serializers.ValidationError(
                f"Insufficient stock. Available: {cart_item.product_size.quantity}."
            )
        return value


# =========================================================================
# Wishlist — Read Serializers
# =========================================================================

class WishlistItemReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for a wishlist product.
    """

    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    price = serializers.DecimalField(
        source='product.price', max_digits=10, decimal_places=2, read_only=True,
    )
    compare_at_price = serializers.DecimalField(
        source='product.compare_at_price', max_digits=10, decimal_places=2,
        read_only=True, allow_null=True,
    )
    is_in_stock = serializers.BooleanField(
        source='product.is_in_stock', read_only=True,
    )

    class Meta:
        model = WishlistItem
        fields = [
            'id',
            'product_id',
            'product_name',
            'product_slug',
            'product_image',
            'price',
            'compare_at_price',
            'is_in_stock',
            'added_at',
        ]
        read_only_fields = fields

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.main_image and request:
            return request.build_absolute_uri(obj.product.main_image.url)
        elif obj.product.main_image:
            return obj.product.main_image.url
        return None


class WishlistReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the entire wishlist.
    """

    items = WishlistItemReadSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ['id', 'items', 'item_count', 'updated_at']
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.items.count()


# =========================================================================
# Wishlist — Write Serializer
# =========================================================================

class AddToWishlistSerializer(serializers.Serializer):
    """
    Validates input for adding a product to the wishlist.

    No size required.  Prevents duplicate entries.
    """

    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        """Ensure the product exists and is active."""
        try:
            product = Product.objects.get(pk=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        if not product.is_active:
            raise serializers.ValidationError("This product is currently unavailable.")

        # Check for duplicate
        user = self.context['request'].user
        try:
            wishlist = Wishlist.objects.get(user=user)
            if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
                raise serializers.ValidationError(
                    "This product is already in your wishlist."
                )
        except Wishlist.DoesNotExist:
            pass  # No wishlist yet — will be created

        return value

    def create(self, validated_data):
        """Create a wishlist item (and wishlist if needed)."""
        user = self.context['request'].user
        product = Product.objects.get(pk=validated_data['product_id'])

        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product,
        )
        return wishlist_item
