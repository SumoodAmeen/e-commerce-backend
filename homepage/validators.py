"""
Validators for Homepage Hero media uploads.

Video: MP4, WEBM only, max 50MB
Image: Uses catalog validators (JPG, PNG, WEBP, max 5MB)
"""

import os
import mimetypes
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Allowed video extensions and MIME types
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm'}
ALLOWED_VIDEO_MIME_TYPES = {'video/mp4', 'video/webm'}

# Maximum video size (50MB)
MAX_VIDEO_SIZE = 50 * 1024 * 1024


def validate_video_file_extension(value):
    """Validate video has allowed extension."""
    if not value:
        return
    
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError(
            _('Unsupported video type. Allowed: MP4, WEBM.'),
            code='invalid_extension'
        )


def validate_video_file_size(value):
    """Validate video does not exceed max size."""
    if not value:
        return
    
    file_size = value.size if hasattr(value, 'size') else len(value.read())
    if file_size > MAX_VIDEO_SIZE:
        max_mb = MAX_VIDEO_SIZE / (1024 * 1024)
        raise ValidationError(
            _('Video size exceeds %(max_size)s MB limit.'),
            code='file_too_large',
            params={'max_size': int(max_mb)}
        )


def validate_video_mime_type(value):
    """Validate actual MIME type of video file."""
    if not value:
        return
    
    if hasattr(value, 'seek'):
        value.seek(0)
    
    try:
        import magic
        file_header = value.read(2048)
        value.seek(0)
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_header)
    except ImportError:
        detected_mime, _ = mimetypes.guess_type(value.name)
    
    if detected_mime not in ALLOWED_VIDEO_MIME_TYPES:
        raise ValidationError(
            _('Invalid video format. File content must be MP4 or WEBM.'),
            code='invalid_mime_type'
        )


def validate_video(value):
    """Combined video validator."""
    validate_video_file_extension(value)
    validate_video_file_size(value)
    validate_video_mime_type(value)
