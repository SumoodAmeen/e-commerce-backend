"""
HomepageHero singleton model.

Singleton enforcement:
- save() forces pk=1
- delete() is disabled
- Admin has no add/delete permissions
"""

import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

from catalog.validators import validate_image
from .validators import validate_video


def hero_desktop_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"homepage/hero/desktop_{uuid.uuid4().hex}{ext}"


def hero_desktop_video_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"homepage/hero/desktop_video_{uuid.uuid4().hex}{ext}"


def hero_mobile_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"homepage/hero/mobile_{uuid.uuid4().hex}{ext}"


def hero_mobile_video_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"homepage/hero/mobile_video_{uuid.uuid4().hex}{ext}"


class HomepageHero(models.Model):
    """
    Singleton model for the homepage hero section.
    
    Only ONE record exists. Admin can only UPDATE, not add or delete.
    """
    
    # Desktop media (optional)
    desktop_image = models.ImageField(
        _('desktop image (optional)'),
        upload_to=hero_desktop_image_path,
        validators=[validate_image],
        blank=True,
        null=True,
        help_text=_('Optional desktop image. Allowed: JPG, PNG, WEBP. Max: 5MB.')
    )
    
    desktop_video = models.FileField(
        _('desktop video (optional)'),
        upload_to=hero_desktop_video_path,
        validators=[validate_video],
        blank=True,
        null=True,
        help_text=_('Optional desktop video. Allowed: MP4, WEBM. Max: 50MB.')
    )
    
    # Mobile media (required)
    mobile_image = models.ImageField(
        _('mobile image (required)'),
        upload_to=hero_mobile_image_path,
        validators=[validate_image],
        help_text=_('Required mobile image. Allowed: JPG, PNG, WEBP. Max: 5MB.')
    )
    
    mobile_video = models.FileField(
        _('mobile video (required)'),
        upload_to=hero_mobile_video_path,
        validators=[validate_video],
        help_text=_('Required mobile video. Allowed: MP4, WEBM. Max: 50MB.')
    )
    
    # System fields
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('If unchecked, hero section will not be displayed.')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('homepage hero')
        verbose_name_plural = _('homepage hero')
    
    def __str__(self):
        return "Homepage Hero"
    
    def save(self, *args, **kwargs):
        """
        Singleton enforcement: always use pk=1.
        Also clears cache on save.
        """
        self.pk = 1
        super().save(*args, **kwargs)
        # Clear cached hero data
        cache.delete('homepage_hero')
    
    def delete(self, *args, **kwargs):
        """
        Prevent deletion of the singleton.
        """
        pass  # Do nothing - deletion is not allowed
    
    @classmethod
    def load(cls):
        """
        Load the singleton instance. Creates one if it doesn't exist.
        """
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    @property
    def desktop_image_url(self):
        if self.desktop_image:
            return self.desktop_image.url
        return None
    
    @property
    def desktop_video_url(self):
        if self.desktop_video:
            return self.desktop_video.url
        return None
    
    @property
    def mobile_image_url(self):
        if self.mobile_image:
            return self.mobile_image.url
        return None
    
    @property
    def mobile_video_url(self):
        if self.mobile_video:
            return self.mobile_video.url
        return None
