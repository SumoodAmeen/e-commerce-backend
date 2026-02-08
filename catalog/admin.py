"""
Django Admin configuration for the Collection model.

Features:
- List view with thumbnails, name, is_active, created_at
- Search by name
- Filter by is_active and created_at
- Bulk actions: activate/deactivate
- Permission-based access control
"""

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Collection model.
    """
    
    # List display configuration
    list_display = [
        'name',
        'image_thumbnail',
        'is_active',
        'created_at',
        'updated_at',
    ]
    
    # List display links
    list_display_links = ['name']
    
    # Editable fields in list view
    list_editable = ['is_active']
    
    # Search configuration
    search_fields = ['name', 'slug']
    
    # Filter configuration
    list_filter = [
        'is_active',
        ('created_at', admin.DateFieldListFilter),
    ]
    
    # Ordering
    ordering = ['-created_at']
    
    # Pagination
    list_per_page = 25
    
    # Read-only fields (slug is auto-generated)
    readonly_fields = ['slug', 'created_at', 'updated_at', 'image_preview']
    
    # Fieldsets for detail view
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'is_active')
        }),
        (_('Image'), {
            'fields': ('image', 'image_preview'),
            'description': _('Allowed formats: JPG, PNG, WEBP. Max size: 5MB.')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Date hierarchy for quick filtering
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['activate_selected', 'deactivate_selected']
    
    def image_thumbnail(self, obj):
        """
        Display a small thumbnail in the list view.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return mark_safe(
            '<span style="color: #999;">No image</span>'
        )
    image_thumbnail.short_description = _('Image')
    image_thumbnail.admin_order_field = 'image'
    
    def image_preview(self, obj):
        """
        Display a larger image preview in the detail view.
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.image.url
            )
        return mark_safe(
            '<span style="color: #999;">No image uploaded</span>'
        )
    image_preview.short_description = _('Image Preview')
    
    @admin.action(description=_('Activate selected collections'))
    def activate_selected(self, request, queryset):
        """
        Bulk action to activate selected collections.
        """
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            _('%(count)d collection(s) successfully activated.') % {'count': updated}
        )
    
    @admin.action(description=_('Deactivate selected collections'))
    def deactivate_selected(self, request, queryset):
        """
        Bulk action to deactivate selected collections.
        """
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            _('%(count)d collection(s) successfully deactivated.') % {'count': updated}
        )
    
    def has_add_permission(self, request):
        """
        Only staff/superusers can add collections.
        """
        return request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        """
        Only staff/superusers can change collections.
        """
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        """
        Only staff/superusers can delete collections.
        """
        return request.user.is_staff
    
    def has_view_permission(self, request, obj=None):
        """
        Only staff/superusers can view collections in admin.
        """
        return request.user.is_staff
