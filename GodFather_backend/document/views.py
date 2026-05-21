
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
import os

from .models import Document
from .serializers import DocumentSerializer
from .tasks import process_document_task, delete_document_index_task
from .utils.elasticsearch_service import ElasticsearchService
from .utils.embedding_service import EmbeddingService
from django.conf import settings

es_service = ElasticsearchService()
embedding_service = EmbeddingService()


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Document.objects.none()
        return Document.objects.filter(uploaded_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Upload a PDF document for indexing",
        manual_parameters=[
            openapi.Parameter(
                'file', 
                openapi.IN_FORM, 
                type=openapi.TYPE_FILE, 
                required=True,
                description="PDF file to upload"
            ),
            openapi.Parameter(
                'title', 
                openapi.IN_FORM, 
                type=openapi.TYPE_STRING, 
                required=False,
                description="Document title (optional, uses filename if not provided)"
            ),
        ],
        responses={
            201: DocumentSerializer,
            400: "Invalid file or missing parameters"
        },
        # Important: Specify consumes for file upload
        consumes=['multipart/form-data']
    )
    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        title = request.data.get('title', '').strip()
        
        if not file:
            return Response({"detail": "File is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not title:
            title = os.path.splitext(file.name)[0]
        
        # Create document record
        document = Document.objects.create(
            title=title,
            file=file,
            uploaded_by=request.user,
            file_size=file.size,
            elastic_index_name=es_service.generate_index_name(0, file.name)
        )
        
        # Update with actual document ID
        document.elastic_index_name = es_service.generate_index_name(document.id, file.name)
        document.save()
        
        # Trigger async processing
        process_document_task.delay(document.id)
        
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        
        # Trigger async index deletion
        delete_document_index_task.delay(document.elastic_index_name, document.file.path)

        # Now delete the DB record
        self.perform_destroy(document)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Search within a specific document",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'query': openapi.Schema(type=openapi.TYPE_STRING, description="Search query"),
                'search_type': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['vector', 'keyword', 'hybrid'],
                    description="Type of search to perform"
                ),
                'top_k': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of results", default=5),
            },
            required=['query']
        ),
        responses={
            200: openapi.Response('Search results'),
            400: "Invalid query",
            404: "Document not indexed"
        }
    )
    @action(detail=True, methods=['post'])
    def search(self, request, pk=None):
        document = self.get_object()
        
        if not document.is_indexed:
            return Response(
                {"detail": "Document is still being indexed. Please try again later."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = request.data.get('query', '').strip()
        search_type = request.data.get('search_type', 'hybrid')
        top_k = request.data.get('top_k', 5)
        
        if not query:
            return Response({"detail": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if search_type == 'keyword':
                results = es_service.keyword_search(document.elastic_index_name, query, top_k)
            elif search_type == 'vector':
                query_embedding = embedding_service.generate_embedding(query)
                results = es_service.vector_search(document.elastic_index_name, query_embedding, top_k)
            else:  # hybrid
                query_embedding = embedding_service.generate_embedding(query)
                results = es_service.hybrid_search(
                    document.elastic_index_name, 
                    query, 
                    query_embedding, 
                    top_k
                )
            
            return Response({
                "document_id": document.id,
                "document_title": document.title,
                "search_type": search_type,
                "results": results
            })
        except Exception as e:
            return Response(
                {"detail": f"Search failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )