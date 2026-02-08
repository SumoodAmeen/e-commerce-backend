"""
Django Admin configuration for ContactInfo.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ContactInfo


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """
    Admin for ContactInfo with full CRUD.
    """
    
    list_display = [
        'contact_number',
        'whatsapp_number',
        'is_active',
        'created_at',
    ]
    
    list_display_links = ['contact_number']
    
    list_editable = ['is_active']
    
    list_filter = ['is_active', 'created_at']
    
    search_fields = ['contact_number', 'whatsapp_number']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Contact Details'), {
            'fields': ('contact_number', 'whatsapp_number'),
        }),
        (_('Social Links'), {
            'fields': (
                'whatsapp_link',
                'instagram_link',
                'youtube_link',
                'x_link',
                'linkedin_link',
            ),
            'description': _('All social links are optional. Must use https:// URLs.')
        }),
        (_('Settings'), {
            'fields': ('is_active',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-created_at']
    
    list_per_page = 25
