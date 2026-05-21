from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.conf import settings

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    elastic_index_name = models.CharField(max_length=255, unique=True)
    total_chunks = models.IntegerField(default=0) 
    is_indexed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-uploaded_at']),
            models.Index(fields=['elastic_index_name']),
        ]
    
    def __str__(self):
        return self.title
