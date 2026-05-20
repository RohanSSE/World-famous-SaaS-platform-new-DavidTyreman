from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'uploaded_by', 'uploaded_by_name', 
                  'uploaded_at', 'file_size', 'total_chunks', 'is_indexed']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_size', 'total_chunks', 'is_indexed']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
