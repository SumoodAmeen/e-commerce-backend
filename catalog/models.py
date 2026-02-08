"""
Collection model for the e-commerce catalog.

Security considerations:
- Slug auto-generation with collision handling
- Image validation at model level
- Timestamps for audit trail
"""

import secrets
import string
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .validators import validate_image


def generate_unique_slug(name, model_class, max_length=300):
    """
    Generate a unique slug from the given name.
    
    If a collision occurs, appends a random suffix to ensure uniqueness.
    This prevents IDOR attacks via predictable slug enumeration.
    """
    base_slug = slugify(name)[:max_length - 10]  # Leave room for suffix
    slug = base_slug
    
    # Check for collision and generate unique suffix if needed
    counter = 0
    while model_class.objects.filter(slug=slug).exists():
        counter += 1
        # Generate a random suffix for unpredictability
        suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        slug = f"{base_slug}-{suffix}"
        
        # Safety limit to prevent infinite loop
        if counter > 100:
            raise ValueError("Unable to generate unique slug after 100 attempts")
    
    return slug


def collection_image_upload_path(instance, filename):
    """
    Generate upload path for collection images.
    
    Uses the collection's slug (or a temporary identifier) to organize files.
    This keeps media files organized and prevents filename collisions.
    """
    import os
    import uuid
    
    # Get file extension safely
    ext = os.path.splitext(filename)[1].lower()
    
    # Generate a unique filename to prevent overwrites and expose original names
    unique_name = f"{uuid.uuid4().hex}{ext}"
    
    # Organize by collections folder
    return f"collections/{unique_name}"


class Collection(models.Model):
    """
    Represents a product collection in the e-commerce catalog.
    
    Collections are used to group products (e.g., "Summer Collection", 
    "Electronics", "Best Sellers").
    """
    
    name = models.CharField(
        _('name'),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Unique name for this collection.')
    )
    
    image = models.ImageField(
        _('image'),
        upload_to=collection_image_upload_path,
        validators=[validate_image],
        help_text=_('Collection image. Allowed formats: JPG, PNG, WEBP. Max size: 5MB.')
    )
    
    slug = models.SlugField(
        _('slug'),
        max_length=300,
        unique=True,
        db_index=True,
        editable=False,  # Prevent manual manipulation
        help_text=_('Auto-generated URL-safe identifier.')
    )
    
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        db_index=True,
        help_text=_('Designates whether this collection should be displayed to customers.')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('Timestamp when the collection was created.')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('Timestamp when the collection was last updated.')
    )
    
    class Meta:
        verbose_name = _('collection')
        verbose_name_plural = _('collections')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug on creation.
        """
        if not self.slug:
            self.slug = generate_unique_slug(self.name, Collection)
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Model-level validation.
        """
        super().clean()
        # Additional custom validation can be added here
    
    @property
    def image_url(self):
        """
        Returns the full URL for the collection image.
        Returns None if no image is set.
        """
        if self.image:
            return self.image.url
        return None


# =============================================================================
# Product Models
# =============================================================================

def product_image_upload_path(instance, filename):
    """
    Generate upload path for product main images.
    """
    import os
    import uuid
    
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"products/{unique_name}"


def product_gallery_upload_path(instance, filename):
    """
    Generate upload path for product gallery images.
    """
    import os
    import uuid
    
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"products/gallery/{unique_name}"


class Product(models.Model):
    """
    Represents a product in the e-commerce catalog.
    
    Each product belongs to exactly one Collection.
    Products have inventory managed through ProductSize.
    """
    
    collection = models.ForeignKey(
        Collection,
        on_delete=models.PROTECT,  # Prevent accidental deletion of collections with products
        related_name='products',
        verbose_name=_('collection'),
        help_text=_('The collection this product belongs to.')
    )
    
    name = models.CharField(
        _('name'),
        max_length=255,
        db_index=True,
        help_text=_('Product name.')
    )
    
    slug = models.SlugField(
        _('slug'),
        max_length=300,
        unique=True,
        db_index=True,
        editable=False,
        help_text=_('Auto-generated URL-safe identifier.')
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Detailed product description.')
    )
    
    material_info = models.TextField(
        _('material info'),
        blank=True,
        default='',
        help_text=_('Material and care instructions.')
    )
    
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Current selling price.')
    )
    
    compare_at_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Original price for showing discounts. Must be >= price.')
    )
    
    main_image = models.ImageField(
        _('main image'),
        upload_to=product_image_upload_path,
        validators=[validate_image],
        help_text=_('Main product image for listings. Allowed: JPG, PNG, WEBP. Max: 5MB.')
    )
    
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        db_index=True,
        help_text=_('Designates whether this product is visible to customers.')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['collection', 'is_active', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug on creation.
        """
        if not self.slug:
            self.slug = generate_unique_slug(self.name, Product)
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Model-level validation.
        """
        from django.core.exceptions import ValidationError
        super().clean()
        
        # Validate compare_at_price >= price
        if self.compare_at_price is not None and self.price is not None:
            if self.compare_at_price < self.price:
                raise ValidationError({
                    'compare_at_price': _('Compare at price must be greater than or equal to the selling price.')
                })
        
        # Validate collection is active (for new products or collection changes)
        if self.collection_id:
            try:
                collection = Collection.objects.get(pk=self.collection_id)
                if not collection.is_active:
                    raise ValidationError({
                        'collection': _('Cannot assign product to an inactive collection.')
                    })
            except Collection.DoesNotExist:
                raise ValidationError({
                    'collection': _('Selected collection does not exist.')
                })
    
    @property
    def main_image_url(self):
        """Returns the URL for the main product image."""
        if self.main_image:
            return self.main_image.url
        return None
    
    @property
    def total_stock(self):
        """Returns total stock across all sizes."""
        return self.sizes.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def is_in_stock(self):
        """Returns True if any size has stock."""
        return self.sizes.filter(quantity__gt=0).exists()


class ProductImage(models.Model):
    """
    Gallery images for a product.
    
    Allows multiple images per product with ordering support.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name=_('product')
    )
    
    image = models.ImageField(
        _('image'),
        upload_to=product_gallery_upload_path,
        validators=[validate_image],
        help_text=_('Gallery image. Allowed: JPG, PNG, WEBP. Max: 5MB.')
    )
    
    alt_text = models.CharField(
        _('alt text'),
        max_length=255,
        blank=True,
        default='',
        help_text=_('Alternative text for accessibility.')
    )
    
    position = models.PositiveIntegerField(
        _('position'),
        default=0,
        help_text=_('Display order (lower numbers appear first).')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['position', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.position}"
    
    @property
    def image_url(self):
        """Returns the URL for this gallery image."""
        if self.image:
            return self.image.url
        return None


class ProductSize(models.Model):
    """
    Size and inventory for a product.
    
    Each product can have multiple sizes with individual stock quantities.
    Uses PositiveIntegerField to prevent negative stock.
    """
    
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('XXXL', 'XXXL'),
        ('ONE_SIZE', 'One Size'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sizes',
        verbose_name=_('product')
    )
    
    size = models.CharField(
        _('size'),
        max_length=20,
        choices=SIZE_CHOICES,
        help_text=_('Size option.')
    )
    
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=0,
        help_text=_('Available stock for this size.')
    )
    
    class Meta:
        verbose_name = _('product size')
        verbose_name_plural = _('product sizes')
        ordering = ['size']
        unique_together = [['product', 'size']]  # Prevent duplicate sizes per product
    
    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.quantity})"
    
    @property
    def is_available(self):
        """Returns True if this size is in stock."""
        return self.quantity > 0

