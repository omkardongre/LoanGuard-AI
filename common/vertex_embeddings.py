"""
Vertex AI Embeddings for semantic document search.

Based on Alzora winner pattern for text embeddings.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
EMBEDDING_MODEL = "text-embedding-005"
EMBEDDING_DIMENSION = 768

# Cache
_embedding_model = None


class VertexEmbeddings:
    """
    Vertex AI Text Embeddings client.
    
    Based on Alzora pattern for semantic search.
    """
    
    def __init__(self):
        self._model = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of Vertex AI."""
        if self._initialized:
            return
        
        try:
            import vertexai
            from vertexai.language_models import TextEmbeddingModel
            
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self._model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
            self._initialized = True
            logger.info(f"Vertex AI Embeddings initialized: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Vertex AI initialization failed: {e}")
            self._initialized = False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        self._initialize()
        
        if not self._model:
            logger.warning("Using fallback random embedding")
            return list(np.random.randn(EMBEDDING_DIMENSION).astype(float))
        
        try:
            embeddings = self._model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        self._initialize()
        
        if not self._model:
            return [list(np.random.randn(EMBEDDING_DIMENSION).astype(float)) for _ in texts]
        
        try:
            # Batch embedding (max 250 texts per batch)
            all_embeddings = []
            batch_size = 250
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self._model.get_embeddings(batch)
                all_embeddings.extend([e.values for e in embeddings])
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [None] * len(texts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_similar(
        self,
        query_embedding: List[float],
        document_embeddings: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find most similar documents to a query.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of {id, embedding, metadata} dicts
            top_k: Number of results to return
            
        Returns:
            Top-k similar documents with scores
        """
        results = []
        
        for doc in document_embeddings:
            score = self.compute_similarity(query_embedding, doc["embedding"])
            results.append({
                "id": doc.get("id"),
                "score": score,
                "metadata": doc.get("metadata", {}),
            })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]


# Global instance
_embeddings: Optional[VertexEmbeddings] = None


def get_embeddings() -> VertexEmbeddings:
    """Get or create the global embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = VertexEmbeddings()
    return _embeddings


def embed_document(text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create an embedding for a document with metadata.
    
    Args:
        text: Document text
        metadata: Optional metadata
        
    Returns:
        Document with embedding
    """
    embeddings = get_embeddings()
    embedding = embeddings.embed_text(text)
    
    return {
        "text": text[:500],  # Store truncated text
        "embedding": embedding,
        "metadata": metadata or {},
    }


def semantic_search(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search over documents.
    
    Args:
        query: Search query
        documents: List of documents with embeddings
        top_k: Number of results
        
    Returns:
        Top-k matching documents
    """
    embeddings = get_embeddings()
    query_embedding = embeddings.embed_text(query)
    
    if query_embedding is None:
        return []
    
    return embeddings.find_similar(query_embedding, documents, top_k)
