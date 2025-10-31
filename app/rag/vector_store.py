import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import faiss
import numpy as np
from llama_index.core.schema import Document, NodeWithScore
from llama_index.vector_stores.faiss import FaissVectorStore
from app.rag.embeddings import get_embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing FAISS vector storage"""

    def __init__(self,
                 vector_store_path: str = "vector_store",
                 index_type: str = "flat",
                 dimension: Optional[int] = None):
        """
        Initialize the vector store service

        Args:
            vector_store_path: Path to store vector indices
            index_type: Type of FAISS index ("flat", "ivf", "hnsw")
            dimension: Embedding dimension (auto-detected if None)
        """
        self.vector_store_path = Path(vector_store_path)
        self.index_type = index_type.lower()
        self.embedding_service = get_embedding_service()
        self.dimension = dimension or self.embedding_service.get_embedding_dimension()

        # Create directory if it doesn't exist
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Paths for index files
        self.index_file = self.vector_store_path / f"{self.index_type}_index.faiss"
        self.metadata_file = self.vector_store_path / f"{self.index_type}_metadata.pkl"

        self._faiss_store: Optional[FaissVectorStore] = None
        self._faiss_index: Optional[faiss.Index] = None
        self._document_metadata: List[Dict[str, Any]] = []

        logger.info(f"Initialized VectorStoreService with index_type: {self.index_type}")

    def _create_faiss_index(self) -> faiss.Index:
        """
        Create a new FAISS index based on the specified type

        Returns:
            FAISS index instance
        """
        if self.index_type == "flat":
            # Simple exact search
            index = faiss.IndexFlatIP(self.dimension)
            logger.info("Created FAISS Flat index for exact search")

        elif self.index_type == "ivf":
            # Inverted file with quantization
            nlist = 100  # number of clusters
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            logger.info("Created FAISS IVF index for approximate search")

        elif self.index_type == "hnsw":
            # Hierarchical navigable small world graph
            index = faiss.IndexHNSWFlat(self.dimension, 32)  # M=32 connections per node
            index.hnsw.efConstruction = 200  # construction parameter
            logger.info("Created FAISS HNSW index for graph-based search")

        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        return index

    def _load_or_create_index(self) -> None:
        """
        Load existing index from disk or create a new one
        """
        if self.index_file.exists() and self.metadata_file.exists():
            logger.info("Loading existing FAISS index from disk")
            try:
                # Load FAISS index
                self._faiss_index = faiss.read_index(str(self.index_file))

                # Load metadata
                with open(self.metadata_file, 'rb') as f:
                    self._document_metadata = pickle.load(f)

                logger.info(f"Loaded index with {len(self._document_metadata)} document entries")

            except Exception as e:
                logger.error(f"Failed to load existing index: {str(e)}")
                logger.info("Creating new index instead")
                self._faiss_index = self._create_faiss_index()
                self._document_metadata = []
        else:
            logger.info("Creating new FAISS index")
            self._faiss_index = self._create_faiss_index()
            self._document_metadata = []

        # Create LlamaIndex FaissVectorStore wrapper
        self._faiss_store = FaissVectorStore(faiss_index=self._faiss_index)

    def get_vector_store(self) -> FaissVectorStore:
        """
        Get the FAISS vector store instance

        Returns:
            FaissVectorStore instance
        """
        if self._faiss_store is None:
            self._load_or_create_index()

        return self._faiss_store

    async def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store

        Args:
            documents: List of Document objects to add
        """
        if not documents:
            logger.warning("No documents to add")
            return

        logger.info(f"Adding {len(documents)} documents to vector store")

        try:
            # Ensure index is loaded
            if self._faiss_store is None:
                self._load_or_create_index()

            # Generate embeddings for all documents
            texts = [doc.text for doc in documents]
            embeddings = await self.embedding_service.get_embeddings(texts)

            # Convert to numpy array and normalize
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)  # Normalize for cosine similarity

            # Add to FAISS index
            self._faiss_index.add(embeddings_array)

            # Add document metadata
            for doc in documents:
                metadata = {
                    'doc_id': doc.doc_id,
                    'text': doc.text,
                    'metadata': doc.metadata or {}
                }
                self._document_metadata.append(metadata)

            logger.info(f"Successfully added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {str(e)}")
            raise

    async def search(self,
                    query: str,
                    top_k: int = 5,
                    similarity_threshold: float = 0.7) -> List[NodeWithScore]:
        """
        Search for similar documents

        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of NodeWithScore objects
        """
        if not query.strip():
            return []

        try:
            # Ensure index is loaded
            if self._faiss_store is None:
                self._load_or_create_index()

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)  # Normalize for cosine similarity

            # Search in FAISS index
            scores, indices = self._faiss_index.search(query_array, min(top_k, len(self._document_metadata)))

            # Convert to NodeWithScore objects
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self._document_metadata) and score >= similarity_threshold:
                    metadata = self._document_metadata[idx]

                    # Create Document object
                    doc = Document(
                        text=metadata['text'],
                        doc_id=metadata['doc_id'],
                        metadata=metadata['metadata']
                    )

                    # Create NodeWithScore
                    node_with_score = NodeWithScore(
                        node=doc,
                        score=float(score)
                    )
                    results.append(node_with_score)

            logger.info(f"Found {len(results)} results for query (threshold: {similarity_threshold})")
            return results

        except Exception as e:
            logger.error(f"Failed to search vector store: {str(e)}")
            raise

    def save_index(self) -> None:
        """
        Save the FAISS index and metadata to disk
        """
        if self._faiss_index is None:
            logger.warning("No index to save")
            return

        try:
            # Save FAISS index
            faiss.write_index(self._faiss_index, str(self.index_file))

            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self._document_metadata, f)

            logger.info(f"Saved index with {len(self._document_metadata)} entries to disk")

        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store

        Returns:
            Dictionary with vector store statistics
        """
        if self._faiss_index is None:
            self._load_or_create_index()

        return {
            'index_type': self.index_type,
            'dimension': self.dimension,
            'total_documents': len(self._document_metadata),
            'index_size': self._faiss_index.ntotal,
            'index_file_exists': self.index_file.exists(),
            'metadata_file_exists': self.metadata_file.exists()
        }

    def clear_index(self) -> None:
        """
        Clear all documents from the vector store
        """
        try:
            # Remove index files
            if self.index_file.exists():
                self.index_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()

            # Reset in-memory index
            self._faiss_index = self._create_faiss_index()
            self._document_metadata = []
            self._faiss_store = FaissVectorStore(faiss_index=self._faiss_index)

            logger.info("Cleared vector store")

        except Exception as e:
            logger.error(f"Failed to clear vector store: {str(e)}")
            raise


# Global vector store service instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """
    Get the global vector store service instance

    Returns:
        VectorStoreService instance
    """
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service