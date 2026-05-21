from openai import AzureOpenAI
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Azure OpenAI only: embeddings via AZURE_OPENAI_* env vars."""

    def __init__(self, api_key=None):
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        key = os.getenv('AZURE_OPENAI_API_KEY') or api_key
        if not endpoint or not key:
            raise ValueError(
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY for embeddings."
            )
        self.client = AzureOpenAI(
            azure_endpoint=endpoint.rstrip('/'),
            api_key=key,
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01'),
        )
        self.model = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    
    def generate_embedding(self, text):
        """Generate embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts, batch_size=100):
        """Generate embeddings for multiple texts in batches"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings.extend([item.embedding for item in response.data])
            except Exception as e:
                logger.error(f"Error in batch embedding: {str(e)}")
                raise
        
        return embeddings