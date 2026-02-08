"""
Validators for ContactInfo fields.

- Phone: digits, spaces, +, -, ()
- URL: http/https only, block javascript:/data:
"""

import re
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _


def validate_phone_number(value):
    """
    Validate phone number format.
    Allows: digits, spaces, +, -, (), and dots.
    """
    if not value:
        return
    
    # Remove allowed characters and check if only digits remain
    cleaned = re.sub(r'[\s\+\-\(\)\.]+', '', value)
    
    if not cleaned.isdigit():
        raise ValidationError(
            _('Phone number can only contain digits, spaces, +, -, (), and dots.'),
            code='invalid_phone'
        )
    
    if len(cleaned) < 7 or len(cleaned) > 15:
        raise ValidationError(
            _('Phone number must be between 7 and 15 digits.'),
            code='invalid_phone_length'
        )


def validate_safe_url(value):
    """
    Validate URL is safe (http/https only).
    Blocks javascript:, data:, and other dangerous schemes.
    """
    if not value:
        return
    
    # Check for dangerous schemes
    lower_value = value.lower().strip()
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    
    for scheme in dangerous_schemes:
        if lower_value.startswith(scheme):
            raise ValidationError(
                _('URL scheme "%(scheme)s" is not allowed.'),
                code='unsafe_url',
                params={'scheme': scheme}
            )
    
    # Must start with http:// or https://
    if not (lower_value.startswith('http://') or lower_value.startswith('https://')):
        raise ValidationError(
            _('URL must start with http:// or https://'),
            code='invalid_url_scheme'
        )
    
    # Use Django's URLValidator for format validation
    url_validator = URLValidator()
    url_validator(value)
