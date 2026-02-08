"""
DRF Serializers for HomepageHero.
"""

from rest_framework import serializers
from .models import HomepageHero
from .validators import validate_video


class HomepageHeroSerializer(serializers.ModelSerializer):
    """
    Public serializer for reading hero data.
    Returns absolute URLs for all media.
    """
    
    desktop_image_url = serializers.SerializerMethodField()
    desktop_video_url = serializers.SerializerMethodField()
    mobile_image_url = serializers.SerializerMethodField()
    mobile_video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = HomepageHero
        fields = [
            'desktop_image_url',
            'desktop_video_url',
            'mobile_image_url',
            'mobile_video_url',
            'is_active',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_desktop_image_url(self, obj):
        request = self.context.get('request')
        if obj.desktop_image and request:
            return request.build_absolute_uri(obj.desktop_image.url)
        elif obj.desktop_image:
            return obj.desktop_image.url
        return None
    
    def get_desktop_video_url(self, obj):
        request = self.context.get('request')
        if obj.desktop_video and request:
            return request.build_absolute_uri(obj.desktop_video.url)
        elif obj.desktop_video:
            return obj.desktop_video.url
        return None
    
    def get_mobile_image_url(self, obj):
        request = self.context.get('request')
        if obj.mobile_image and request:
            return request.build_absolute_uri(obj.mobile_image.url)
        elif obj.mobile_image:
            return obj.mobile_image.url
        return None
    
    def get_mobile_video_url(self, obj):
        request = self.context.get('request')
        if obj.mobile_video and request:
            return request.build_absolute_uri(obj.mobile_video.url)
        elif obj.mobile_video:
            return obj.mobile_video.url
        return None


class HomepageHeroUpdateSerializer(serializers.ModelSerializer):
    """
    Admin serializer for updating hero data.
    """
    
    class Meta:
        model = HomepageHero
        fields = [
            'desktop_image',
            'desktop_video',
            'mobile_image',
            'mobile_video',
            'is_active',
        ]
    
    def update(self, instance, validated_data):
        # Delete old files when replacing
        if 'desktop_image' in validated_data and validated_data['desktop_image']:
            if instance.desktop_image:
                instance.desktop_image.delete(save=False)
        
        if 'desktop_video' in validated_data and validated_data['desktop_video']:
            if instance.desktop_video:
                instance.desktop_video.delete(save=False)
        
        if 'mobile_image' in validated_data and validated_data['mobile_image']:
            if instance.mobile_image:
                instance.mobile_image.delete(save=False)
        
        if 'mobile_video' in validated_data and validated_data['mobile_video']:
            if instance.mobile_video:
                instance.mobile_video.delete(save=False)
        
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        return HomepageHeroSerializer(instance, context=self.context).data
