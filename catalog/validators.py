"""
Image validators for secure file upload handling.

Security measures:
1. File extension validation - whitelist approach
2. MIME type validation - validates actual file content
3. File size limit - prevents DoS attacks
"""

import os
import mimetypes
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Allowed image extensions and their MIME types
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}

# Maximum file size in bytes (5MB)
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def validate_image_file_extension(value):
    """
    Validate that the uploaded file has an allowed image extension.
    
    This is a first-line defense that prevents obviously wrong file types
    from being processed further.
    """
    if not value:
        return
    
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _('Unsupported file type. Allowed types: JPG, PNG, WEBP.'),
            code='invalid_extension'
        )


def validate_image_file_size(value):
    """
    Validate that the uploaded file does not exceed the maximum size limit.
    
    This prevents denial-of-service attacks via large file uploads
    and ensures reasonable storage usage.
    """
    if not value:
        return
    
    # Get file size
    file_size = value.size if hasattr(value, 'size') else len(value.read())
    
    if file_size > MAX_IMAGE_SIZE:
        max_mb = MAX_IMAGE_SIZE / (1024 * 1024)
        raise ValidationError(
            _('File size exceeds maximum limit of %(max_size)s MB.'),
            code='file_too_large',
            params={'max_size': max_mb}
        )


def validate_image_mime_type(value):
    """
    Validate the actual MIME type of the uploaded file.
    
    This is a critical security measure that validates the file content,
    not just the extension. It prevents attacks where malicious files
    are renamed to have image extensions.
    
    Note: For production, consider using python-magic for more reliable
    MIME type detection based on file signatures.
    """
    if not value:
        return
    
    # Reset file pointer to beginning
    if hasattr(value, 'seek'):
        value.seek(0)
    
    # Try to get MIME type from file content
    try:
        # Use python-magic if available for more reliable detection
        import magic
        
        # Read first 2048 bytes for MIME detection
        file_header = value.read(2048)
        value.seek(0)  # Reset file pointer
        
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_header)
        
    except ImportError:
        # Fallback to mimetypes module (less reliable but works without dependencies)
        detected_mime, _ = mimetypes.guess_type(value.name)
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('Invalid image format. The file content does not match an allowed image type.'),
            code='invalid_mime_type'
        )


# Combined validator for convenience
def validate_image(value):
    """
    Combined validator that runs all image validation checks.
    Use this as the primary validator for ImageField.
    """
    validate_image_file_extension(value)
    validate_image_file_size(value)
    validate_image_mime_type(value)
