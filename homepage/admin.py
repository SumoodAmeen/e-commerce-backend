"""
Django Admin configuration for HomepageHero.

Singleton enforcement:
- No add permission
- No delete permission
- Update only
"""

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from .models import HomepageHero


@admin.register(HomepageHero)
class HomepageHeroAdmin(admin.ModelAdmin):
    """
    Admin for singleton HomepageHero.
    Only allows updating, not adding or deleting.
    """
    
    list_display = ['__str__', 'is_active', 'updated_at']
    
    readonly_fields = [
        'updated_at',
        'desktop_image_preview',
        'mobile_image_preview',
        'desktop_video_name',
        'mobile_video_name',
    ]
    
    fieldsets = (
        (_('Desktop Media (Optional)'), {
            'fields': (
                'desktop_image',
                'desktop_image_preview',
                'desktop_video',
                'desktop_video_name',
            ),
            'description': _('Desktop image and video are optional. Frontend will prioritize video over image.')
        }),
        (_('Mobile Media (Required)'), {
            'fields': (
                'mobile_image',
                'mobile_image_preview',
                'mobile_video',
                'mobile_video_name',
            ),
            'description': _('Mobile image and video are required.')
        }),
        (_('Settings'), {
            'fields': ('is_active', 'updated_at'),
        }),
    )
    
    def desktop_image_preview(self, obj):
        """Display desktop image preview."""
        if obj.desktop_image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 200px; border-radius: 8px;" />',
                obj.desktop_image.url
            )
        return mark_safe('<span style="color: #999;">No desktop image uploaded</span>')
    desktop_image_preview.short_description = _('Desktop Image Preview')
    
    def mobile_image_preview(self, obj):
        """Display mobile image preview."""
        if obj.mobile_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 400px; border-radius: 8px;" />',
                obj.mobile_image.url
            )
        return mark_safe('<span style="color: #999;">No mobile image uploaded</span>')
    mobile_image_preview.short_description = _('Mobile Image Preview')
    
    def desktop_video_name(self, obj):
        """Display desktop video filename."""
        if obj.desktop_video:
            import os
            filename = os.path.basename(obj.desktop_video.name)
            return format_html(
                '<span style="font-family: monospace;">🎬 {}</span>',
                filename
            )
        return mark_safe('<span style="color: #999;">No desktop video uploaded</span>')
    desktop_video_name.short_description = _('Desktop Video File')
    
    def mobile_video_name(self, obj):
        """Display mobile video filename."""
        if obj.mobile_video:
            import os
            filename = os.path.basename(obj.mobile_video.name)
            return format_html(
                '<span style="font-family: monospace;">🎬 {}</span>',
                filename
            )
        return mark_safe('<span style="color: #999;">No mobile video uploaded</span>')
    mobile_video_name.short_description = _('Mobile Video File')
    
    def has_add_permission(self, request):
        """
        Prevent adding new records. Singleton already exists.
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deleting the singleton record.
        """
        return False
    
    def changelist_view(self, request, extra_context=None):
        """
        Redirect to the singleton edit page instead of showing list.
        """
        from django.shortcuts import redirect
        # Ensure singleton exists
        HomepageHero.load()
        return redirect('admin:homepage_homepagehero_change', 1)
