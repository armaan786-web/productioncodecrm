from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_file_extension(value):
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"]
    extension = str(value).lower()[-4:]

    if extension not in allowed_extensions:
        raise ValidationError(
            _("Unsupported file extension. Please upload a valid file.")
        )
