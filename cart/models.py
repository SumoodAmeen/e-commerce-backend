"""
Cart and Wishlist models for the e-commerce application.

Security considerations:
- OneToOne relationship ensures one cart/wishlist per user
- Quantity validated at model level with MinValueValidator
- unique_together constraints prevent duplicate entries
- CASCADE deletion keeps data clean when users/products are removed
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    """
    Shopping cart — one per user.

    Auto-created when the user adds their first item.
    Persists even when all items are removed.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user'),
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f"Cart — {self.user.username}"

    @property
    def total(self):
        """Computed cart total across all items."""
        return sum(item.subtotal for item in self.items.select_related('product'))


class CartItem(models.Model):
    """
    A single line-item inside a cart.

    The combination of (cart, product, product_size) is unique — adding the
    same product + size again increments quantity instead of creating a
    duplicate row.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart'),
    )

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )

    product_size = models.ForeignKey(
        'catalog.ProductSize',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('size'),
    )

    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_('Must be at least 1.'),
    )

    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = [['cart', 'product', 'product_size']]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name} ({self.product_size.size}) x{self.quantity}"

    @property
    def subtotal(self):
        """Price × quantity for this line item."""
        return self.product.price * self.quantity


# =========================================================================
# Wishlist
# =========================================================================

class Wishlist(models.Model):
    """
    Wishlist — one per user.

    Auto-created when the user adds their first item.
    No size selection required (unlike cart).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
        verbose_name=_('user'),
    )

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('wishlist')
        verbose_name_plural = _('wishlists')

    def __str__(self):
        return f"Wishlist — {self.user.username}"


class WishlistItem(models.Model):
    """
    A product saved to a user's wishlist.

    unique_together on (wishlist, product) prevents duplicates.
    """

    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('wishlist'),
    )

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name=_('product'),
    )

    added_at = models.DateTimeField(_('added at'), auto_now_add=True)

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        unique_together = [['wishlist', 'product']]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.product.name}"
