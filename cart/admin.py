"""
Django Admin configuration for Cart & Wishlist.

Provides internal visibility for customer-support and debugging.
"""

from django.contrib import admin

from .models import Cart, CartItem, Wishlist, WishlistItem


# =========================================================================
# Cart Admin
# =========================================================================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'product_size', 'quantity', 'added_at', 'updated_at')
    can_delete = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'created_at', 'updated_at')
    list_select_related = ('user',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'created_at', 'updated_at')
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_user', 'product', 'product_size', 'quantity', 'added_at')
    list_select_related = ('cart__user', 'product', 'product_size')
    search_fields = ('cart__user__username', 'product__name')
    list_filter = ('added_at',)
    readonly_fields = ('cart', 'product', 'product_size', 'added_at', 'updated_at')

    def cart_user(self, obj):
        return obj.cart.user.username
    cart_user.short_description = 'User'


# =========================================================================
# Wishlist Admin
# =========================================================================

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ('product', 'added_at')
    can_delete = True


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'created_at', 'updated_at')
    list_select_related = ('user',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'created_at', 'updated_at')
    inlines = [WishlistItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist_user', 'product', 'added_at')
    list_select_related = ('wishlist__user', 'product')
    search_fields = ('wishlist__user__username', 'product__name')
    list_filter = ('added_at',)
    readonly_fields = ('wishlist', 'product', 'added_at')

    def wishlist_user(self, obj):
        return obj.wishlist.user.username
    wishlist_user.short_description = 'User'
