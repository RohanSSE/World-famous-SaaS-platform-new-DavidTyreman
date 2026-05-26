from django.contrib import admin

from .models import AIKnowledgeChunk


@admin.register(AIKnowledgeChunk)
class AIKnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("chunk_id", "title", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
