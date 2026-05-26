from openai import AzureOpenAI
import logging
import os

logger = logging.getLogger(__name__)

# Single embedding deployment — must exist in Azure Portal (1536 dimensions).
DEFAULT_EMBEDDING_DEPLOYMENT = "text-embedding-3-small"


def _normalize_azure_endpoint(endpoint: str) -> str:
    """
    Azure resource root only, e.g. https://<resource>.openai.azure.com
    Fixes .env values that mistakenly use the chat/completions deployment URL.
    """
    endpoint = endpoint.strip().rstrip("/")
    if "/openai/deployments/" in endpoint or endpoint.endswith("/chat/completions"):
        from urllib.parse import urlparse

        parsed = urlparse(endpoint)
        return f"{parsed.scheme}://{parsed.netloc}"
    if "/openai/" in endpoint:
        return endpoint.split("/openai")[0].rstrip("/")
    return endpoint


class EmbeddingService:
    """Azure OpenAI embeddings via AZURE_OPENAI_EMBEDDING_DEPLOYMENT (text-embedding-3-small)."""

    def __init__(self, api_key=None):
        endpoint = _normalize_azure_endpoint(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        key = os.getenv("AZURE_OPENAI_API_KEY") or api_key
        if not endpoint or not key:
            raise ValueError(
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY for embeddings."
            )
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
        self.model = os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            DEFAULT_EMBEDDING_DEPLOYMENT,
        ).strip()
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=api_version,
        )
        logger.info("Using embedding deployment: %s", self.model)

    def generate_embedding(self, text):
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Error generating embedding: %s", e)
            raise

    def generate_embeddings_batch(self, texts, batch_size=100):
        """Generate embeddings for multiple texts in batches."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )
                embeddings.extend([item.embedding for item in response.data])
            except Exception as e:
                logger.error("Error in batch embedding: %s", e)
                raise

        return embeddings
