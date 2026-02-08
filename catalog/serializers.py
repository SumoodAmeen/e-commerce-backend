"""
DRF Serializers for the Collection model.

Security considerations:
- Separate serializers for read vs write operations
- Explicit field declarations (no shortcuts)
- Validation at serializer level as second defense layer
"""

from rest_framework import serializers
from django.utils.text import slugify

from .models import Collection
from .validators import (
    validate_image_file_extension,
    validate_image_file_size,
    validate_image_mime_type,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE,
)


class CollectionListSerializer(serializers.ModelSerializer):
    """
    Serializer for public collection listing.
    
    Returns minimal data optimized for frontend listing pages.
    Only active collections should be serialized with this.
    """
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'slug', 'image_url']
        read_only_fields = fields
    
    def get_image_url(self, obj):
        """
        Returns absolute URL for the collection image.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class CollectionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for collection detail view.
    
    Returns all public fields for a single collection.
    """
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'image_url',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_image_url(self, obj):
        """
        Returns absolute URL for the collection image.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class CollectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new collections.
    
    Validates all input data before allowing creation.
    Used by admin/staff users only.
    """
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'image', 'is_active']
        read_only_fields = ['id']
    
    def validate_name(self, value):
        """
        Validate the collection name.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Collection name cannot be empty.")
        
        # Normalize whitespace
        value = ' '.join(value.split())
        
        # Check length
        if len(value) < 2:
            raise serializers.ValidationError("Collection name must be at least 2 characters.")
        
        if len(value) > 255:
            raise serializers.ValidationError("Collection name cannot exceed 255 characters.")
        
        # Check for uniqueness (case-insensitive)
        if Collection.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A collection with this name already exists.")
        
        return value
    
    def validate_image(self, value):
        """
        Additional image validation at serializer level.
        This complements model-level validation.
        """
        if not value:
            raise serializers.ValidationError("Image is required.")
        
        # Run all validators
        try:
            validate_image_file_extension(value)
            validate_image_file_size(value)
            validate_image_mime_type(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def create(self, validated_data):
        """
        Create and return a new Collection instance.
        """
        return Collection.objects.create(**validated_data)
    
    def to_representation(self, instance):
        """
        Return detailed representation after creation.
        """
        return CollectionDetailSerializer(instance, context=self.context).data


class CollectionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing collections.
    
    Allows partial updates and validates changed fields.
    Used by admin/staff users only.
    """
    
    class Meta:
        model = Collection
        fields = ['id', 'name', 'image', 'is_active']
        read_only_fields = ['id']
        extra_kwargs = {
            'name': {'required': False},
            'image': {'required': False},
            'is_active': {'required': False},
        }
    
    def validate_name(self, value):
        """
        Validate the collection name, checking for uniqueness excluding current instance.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Collection name cannot be empty.")
        
        # Normalize whitespace
        value = ' '.join(value.split())
        
        # Check length
        if len(value) < 2:
            raise serializers.ValidationError("Collection name must be at least 2 characters.")
        
        if len(value) > 255:
            raise serializers.ValidationError("Collection name cannot exceed 255 characters.")
        
        # Check for uniqueness excluding current instance
        instance = self.instance
        queryset = Collection.objects.filter(name__iexact=value)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A collection with this name already exists.")
        
        return value
    
    def validate_image(self, value):
        """
        Validate image if provided.
        """
        if value:
            try:
                validate_image_file_extension(value)
                validate_image_file_size(value)
                validate_image_mime_type(value)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        
        return value
    
    def update(self, instance, validated_data):
        """
        Update and return an existing Collection instance.
        """
        # Update name and regenerate slug if name changed
        new_name = validated_data.get('name')
        if new_name and new_name != instance.name:
            instance.name = new_name
            # Regenerate slug for new name
            from .models import generate_unique_slug
            instance.slug = generate_unique_slug(new_name, Collection)
        
        # Update other fields
        if 'image' in validated_data:
            # Delete old image file to prevent orphaned files
            if instance.image:
                instance.image.delete(save=False)
            instance.image = validated_data['image']
        
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """
        Return detailed representation after update.
        """
        return CollectionDetailSerializer(instance, context=self.context).data


class CollectionAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for admin listing view.
    
    Returns all fields including timestamps for admin dashboard.
    """
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'slug',
            'image_url',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_image_url(self, obj):
        """
        Returns absolute URL for the collection image.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


# =============================================================================
# Product Serializers
# =============================================================================

from .models import Product, ProductImage, ProductSize


class ProductSizeSerializer(serializers.ModelSerializer):
    """
    Serializer for product sizes/inventory.
    """
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'quantity', 'is_available']
        read_only_fields = ['id', 'is_available']


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product gallery images.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'position']
        read_only_fields = ['id', 'image_url']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for public product listing.
    Minimal fields for fast loading.
    """
    main_image_url = serializers.SerializerMethodField()
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    collection_slug = serializers.CharField(source='collection.slug', read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'price',
            'compare_at_price',
            'main_image_url',
            'collection_name',
            'collection_slug',
            'is_in_stock',
        ]
        read_only_fields = fields
    
    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if obj.main_image and request:
            return request.build_absolute_uri(obj.main_image.url)
        elif obj.main_image:
            return obj.main_image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for product detail view.
    Includes all fields, gallery, and sizes.
    """
    main_image_url = serializers.SerializerMethodField()
    collection = CollectionListSerializer(read_only=True)
    gallery_images = ProductImageSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    is_in_stock = serializers.ReadOnlyField()
    total_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'material_info',
            'price',
            'compare_at_price',
            'main_image_url',
            'collection',
            'gallery_images',
            'sizes',
            'is_in_stock',
            'total_stock',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
    
    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if obj.main_image and request:
            return request.build_absolute_uri(obj.main_image.url)
        elif obj.main_image:
            return obj.main_image.url
        return None


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating products.
    Validates collection is active.
    """
    sizes = ProductSizeSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'collection',
            'name',
            'description',
            'material_info',
            'price',
            'compare_at_price',
            'main_image',
            'is_active',
            'sizes',
        ]
        read_only_fields = ['id']
    
    def validate_collection(self, value):
        """Validate collection is active."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign product to an inactive collection.")
        return value
    
    def validate_main_image(self, value):
        """Validate main image."""
        if value:
            validate_image_file_extension(value)
            validate_image_file_size(value)
            validate_image_mime_type(value)
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        price = data.get('price')
        compare_at_price = data.get('compare_at_price')
        
        if compare_at_price is not None and price is not None:
            if compare_at_price < price:
                raise serializers.ValidationError({
                    'compare_at_price': 'Compare at price must be >= selling price.'
                })
        return data
    
    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])
        product = Product.objects.create(**validated_data)
        
        for size_data in sizes_data:
            ProductSize.objects.create(product=product, **size_data)
        
        return product
    
    def to_representation(self, instance):
        return ProductDetailSerializer(instance, context=self.context).data


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating products.
    """
    sizes = ProductSizeSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'collection',
            'name',
            'description',
            'material_info',
            'price',
            'compare_at_price',
            'main_image',
            'is_active',
            'sizes',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'collection': {'required': False},
            'name': {'required': False},
            'description': {'required': False},
            'main_image': {'required': False},
            'price': {'required': False},
        }
    
    def validate_collection(self, value):
        """Validate collection is active."""
        if value and not value.is_active:
            raise serializers.ValidationError("Cannot assign product to an inactive collection.")
        return value
    
    def validate_main_image(self, value):
        """Validate main image if provided."""
        if value:
            validate_image_file_extension(value)
            validate_image_file_size(value)
            validate_image_mime_type(value)
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        price = data.get('price', self.instance.price if self.instance else None)
        compare_at_price = data.get('compare_at_price')
        
        if compare_at_price is not None and price is not None:
            if compare_at_price < price:
                raise serializers.ValidationError({
                    'compare_at_price': 'Compare at price must be >= selling price.'
                })
        return data
    
    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            if attr == 'main_image' and value:
                # Delete old image
                if instance.main_image:
                    instance.main_image.delete(save=False)
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update sizes if provided
        if sizes_data is not None:
            # Clear existing and recreate
            instance.sizes.all().delete()
            for size_data in sizes_data:
                ProductSize.objects.create(product=instance, **size_data)
        
        return instance
    
    def to_representation(self, instance):
        return ProductDetailSerializer(instance, context=self.context).data

