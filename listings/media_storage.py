"""
Media Files Management for Django

This module helps ensure media files are properly handled in both
development and production environments.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

class PersistentMediaStorage(FileSystemStorage):
    """
    Custom storage class that ensures media files are saved
    with proper permissions and backup considerations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure media directory exists
        if not os.path.exists(self.location):
            os.makedirs(self.location, mode=0o755, exist_ok=True)
    
    def save(self, name, content):
        """
        Save file with proper permission settings
        """
        # Call parent save method
        saved_name = super().save(name, content)
        
        # Set proper permissions (755 for security)
        file_path = os.path.join(self.location, saved_name)
        try:
            os.chmod(file_path, 0o644)
        except OSError as e:
            print(f"Warning: Could not set file permissions: {e}")
        
        return saved_name


def get_media_file_path(instance, filename):
    """
    Generate organized file paths for media uploads
    Format: media/[model_name]/[year]/[month]/[filename]
    """
    from datetime import datetime
    
    model_name = instance.__class__.__name__.lower()
    year = datetime.now().year
    month = datetime.now().month
    
    return f'{model_name}/{year}/{month}/{filename}'


# Configuration for robust media handling
MEDIA_CONFIG = {
    'max_upload_size': 5 * 1024 * 1024,  # 5MB per file
    'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif'],
    'auto_backup': True,
    'backup_interval': 'daily',
}
