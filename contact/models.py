"""
ContactInfo model for business contact details and social links.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number, validate_safe_url


class ContactInfo(models.Model):
    """
    Stores business contact information and social media links.
    """
    
    # Contact details
    contact_number = models.CharField(
        _('contact number'),
        max_length=20,
        validators=[validate_phone_number],
        help_text=_('Primary contact number with country code.')
    )
    
    whatsapp_number = models.CharField(
        _('WhatsApp number'),
        max_length=20,
        blank=True,
        default='',
        validators=[validate_phone_number],
        help_text=_('WhatsApp number with country code (optional).')
    )
    
    # Social links (all optional)
    whatsapp_link = models.URLField(
        _('WhatsApp link'),
        max_length=500,
        blank=True,
        default='',
        validators=[validate_safe_url],
        help_text=_('WhatsApp click-to-chat URL (e.g., https://wa.me/1234567890)')
    )
    
    instagram_link = models.URLField(
        _('Instagram link'),
        max_length=500,
        blank=True,
        default='',
        validators=[validate_safe_url],
        help_text=_('Instagram profile URL.')
    )
    
    youtube_link = models.URLField(
        _('YouTube link'),
        max_length=500,
        blank=True,
        default='',
        validators=[validate_safe_url],
        help_text=_('YouTube channel URL.')
    )
    
    x_link = models.URLField(
        _('X (Twitter) link'),
        max_length=500,
        blank=True,
        default='',
        validators=[validate_safe_url],
        help_text=_('X (formerly Twitter) profile URL.')
    )
    
    linkedin_link = models.URLField(
        _('LinkedIn link'),
        max_length=500,
        blank=True,
        default='',
        validators=[validate_safe_url],
        help_text=_('LinkedIn company or profile URL.')
    )
    
    # System fields
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        db_index=True,
        help_text=_('If unchecked, this contact info will not be displayed.')
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
        verbose_name = _('contact info')
        verbose_name_plural = _('contact info')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contact: {self.contact_number}"
    
    def clean(self):
        """Model-level validation."""
        super().clean()
        
        # Validate URLs that are not empty
        url_fields = [
            'whatsapp_link', 'instagram_link', 'youtube_link',
            'x_link', 'linkedin_link'
        ]
        for field in url_fields:
            value = getattr(self, field, '')
            if value:
                validate_safe_url(value)
