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
