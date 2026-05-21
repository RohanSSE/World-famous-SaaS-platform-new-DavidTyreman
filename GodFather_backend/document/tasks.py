from celery import shared_task
from django.core.files.storage import default_storage
import logging
import os

from .models import Document
from .utils.pdf_processor import PDFProcessor
from .utils.elasticsearch_service import ElasticsearchService
from .utils.embedding_service import EmbeddingService
from django.conf import settings

logger = logging.getLogger(__name__)
pdf_processor = PDFProcessor()
es_service = ElasticsearchService()
embedding_service = EmbeddingService()


@shared_task
def process_document_task(document_id):
    """Process PDF document: extract text, create chunks, generate embeddings, and index"""
    try:
        document = Document.objects.get(id=document_id)
        pdf_path = document.file.path
        
        logger.info(f"Processing document {document_id}: {document.title}")
        
        # Step 1: Extract text from PDF
        text_content = pdf_processor.extract_text_from_pdf(pdf_path)
        
        # Step 2: Create chunks
        chunks = pdf_processor.chunk_text(text_content, document_id)
        
        if not chunks:
            logger.warning(f"No text extracted from document {document_id}")
            return
        
        # Step 3: Generate embeddings for chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        # Step 4: Create Elasticsearch index
        es_service.create_index(document.elastic_index_name)
        
        # Step 5: Index chunks
        success, failed = es_service.index_chunks(document.elastic_index_name, chunks)
        
        # Update document record
        document.total_chunks = len(chunks)
        document.is_indexed = True
        document.save()
        
        logger.info(f"Successfully processed document {document_id}: {success} chunks indexed")
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        # Mark as failed
        try:
            document = Document.objects.get(id=document_id)
            document.is_indexed = False
            document.save()
        except:
            pass


@shared_task
def delete_document_index_task(index_name, file_path):
    """Delete Elasticsearch index and file"""
    try:
        # Delete from Elasticsearch
        es_service.delete_index(index_name)
        logger.info(f"Deleted index: {index_name}")
        
        # Delete file from storage
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        
    except Exception as e:
        logger.error(f"Error deleting document resources: {str(e)}")