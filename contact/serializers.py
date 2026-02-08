"""
DRF Serializers for ContactInfo.
"""

from rest_framework import serializers
from .models import ContactInfo
from .validators import validate_phone_number, validate_safe_url


class ContactInfoSerializer(serializers.ModelSerializer):
    """
    Public serializer for reading contact info.
    """
    
    class Meta:
        model = ContactInfo
        fields = [
            'id',
            'contact_number',
            'whatsapp_number',
            'whatsapp_link',
            'instagram_link',
            'youtube_link',
            'x_link',
            'linkedin_link',
            'is_active',
            'updated_at',
        ]
        read_only_fields = fields


class ContactInfoCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Admin serializer for creating/updating contact info.
    """
    
    class Meta:
        model = ContactInfo
        fields = [
            'id',
            'contact_number',
            'whatsapp_number',
            'whatsapp_link',
            'instagram_link',
            'youtube_link',
            'x_link',
            'linkedin_link',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def validate_contact_number(self, value):
        validate_phone_number(value)
        return value
    
    def validate_whatsapp_number(self, value):
        if value:
            validate_phone_number(value)
        return value
    
    def validate_whatsapp_link(self, value):
        if value:
            validate_safe_url(value)
        return value
    
    def validate_instagram_link(self, value):
        if value:
            validate_safe_url(value)
        return value
    
    def validate_youtube_link(self, value):
        if value:
            validate_safe_url(value)
        return value
    
    def validate_x_link(self, value):
        if value:
            validate_safe_url(value)
        return value
    
    def validate_linkedin_link(self, value):
        if value:
            validate_safe_url(value)
        return value
    
    def to_representation(self, instance):
        return ContactInfoSerializer(instance).data
