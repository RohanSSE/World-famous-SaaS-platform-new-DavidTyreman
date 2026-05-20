from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'uploaded_at', 'file_size', 'total_chunks', 'is_indexed']
    list_filter = ['is_indexed', 'uploaded_at']
    search_fields = ['title', 'uploaded_by__username']
    readonly_fields = ['uploaded_at', 'file_size', 'elastic_index_name', 'total_chunks', 'is_indexed']