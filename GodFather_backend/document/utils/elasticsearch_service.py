from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk
import hashlib
import logging
import ssl

logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self, hosts=None):
        # Use settings hosts if not provided
        if hosts is None:
            from django.conf import settings
            hosts = getattr(settings, 'ELASTICSEARCH_HOSTS', ['http://localhost:9200'])
        
        # Create SSL context to bypass self-signed cert verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # self.es = Elasticsearch(
        #     hosts=hosts,
        #     # use_ssl=True,  # Explicit for HTTPS
        #     verify_certs=False,  # Core fix: Ignore self-signed certs
        #     ssl_show_warn=False,  # Suppress warnings
        #     ssl_context=ssl_context,  # Enforce custom context
        #     basic_auth=('elastic', 'changeme'),  # Add your ES creds here
        #     timeout=30,  # Increase timeout for stability
        #     max_retries=5,  # More retries on transient errors
        #     retry_on_timeout=True,
        # )
        # Simple HTTP client — NO TLS OPTIONS
        self.es = Elasticsearch(
            hosts=hosts,
            timeout=30,
            max_retries=5,
            retry_on_timeout=True,
        )

        
    
    def generate_index_name(self, document_id, filename):
        """Generate unique index name for document"""
        hash_obj = hashlib.md5(f"{document_id}_{filename}".encode())
        return f"doc_{document_id}_{hash_obj.hexdigest()[:8]}"
    
    def create_index(self, index_name):
        """Create Elasticsearch index with vector and text mappings"""
        mapping = {
            "mappings": {
                "properties": {
                    "document_id": {"type": "integer"},
                    "chunk_id": {"type": "integer"},
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1536,  # OpenAI embedding dimension
                        "index": True,
                        "similarity": "cosine"
                    },
                    "page_number": {"type": "integer"},
                    "metadata": {"type": "object"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        try:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=mapping)
                logger.info(f"Created index: {index_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {str(e)}")
            raise
    
    def index_chunks(self, index_name, chunks):
        """Bulk index document chunks with embeddings"""
        actions = [
            {
                "_index": index_name,
                "_id": f"{chunk['chunk_id']}",
                "_source": chunk
            }
            for chunk in chunks
        ]
        
        try:
            success, failed = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Indexed {success} chunks, {len(failed)} failed")
            return success, failed
        except Exception as e:
            logger.error(f"Error bulk indexing: {str(e)}")
            raise
    
    def delete_index(self, index_name):
        """Delete Elasticsearch index"""
        try:
            if self.es.indices.exists(index=index_name):
                self.es.indices.delete(index=index_name)
                logger.info(f"Deleted index: {index_name}")
                return True
            return False
        except NotFoundError:
            logger.warning(f"Index {index_name} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting index {index_name}: {str(e)}")
            raise
    
    def vector_search(self, index_name, query_embedding, top_k=5):
        """Perform vector similarity search"""
        try:
            response = self.es.search(
                index=index_name,
                body={
                    "size": top_k,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": query_embedding}
                            }
                        }
                    }
                }
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Vector search error: {str(e)}")
            return []
    
    def keyword_search(self, index_name, query_text, top_k=5):
        """Perform keyword-based text search"""
        try:
            response = self.es.search(
                index=index_name,
                body={
                    "size": top_k,
                    "query": {
                        "match": {
                            "text": {
                                "query": query_text,
                                "fuzziness": "AUTO"
                            }
                        }
                    },
                    "highlight": {
                        "fields": {
                            "text": {}
                        }
                    }
                }
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            return []
    
    def hybrid_search(self, index_name, query_text, query_embedding, top_k=5, vector_weight=0.7):
        """Perform hybrid search combining vector and keyword search"""
        vector_results = self.vector_search(index_name, query_embedding, top_k * 2)
        keyword_results = self.keyword_search(index_name, query_text, top_k * 2)
        
        # Combine and re-rank results
        combined = {}
        for i, result in enumerate(vector_results):
            chunk_id = result['chunk_id']
            combined[chunk_id] = {
                'data': result,
                'score': (len(vector_results) - i) * vector_weight
            }
        
        for i, result in enumerate(keyword_results):
            chunk_id = result['chunk_id']
            if chunk_id in combined:
                combined[chunk_id]['score'] += (len(keyword_results) - i) * (1 - vector_weight)
            else:
                combined[chunk_id] = {
                    'data': result,
                    'score': (len(keyword_results) - i) * (1 - vector_weight)
                }
        
        # Sort by combined score
        sorted_results = sorted(combined.values(), key=lambda x: x['score'], reverse=True)
        # Return score WITH the data so it can be used for sorting later
        return [
            {**item['data'], 'score': item['score']} 
            for item in sorted_results[:top_k]
        ]