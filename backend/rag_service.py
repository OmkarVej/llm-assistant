"""
A2Z IntelliBrain - RAG (Retrieval-Augmented Generation) Service
Implements the Vector Store and knowledge retrieval layer
"""
import os
import pickle
from typing import List, Dict, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available. Install with: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")

# Fallback to OpenAI embeddings if sentence-transformers not available
import openai


class VectorStore:
    """Vector Store for A2Z knowledge base using FAISS"""
    
    def __init__(self, embedding_dim: int = 384, index_path: Optional[str] = None):
        self.embedding_dim = embedding_dim
        self.index_path = index_path or os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'vector_store.index')
        self.metadata_path = index_path.replace('.index', '.metadata.pkl') if index_path else \
            os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'vector_store.metadata.pkl')
        
        # Initialize embedding model
        self.embedding_model = None
        self.use_openai_embeddings = False
        self._init_embedding_model()
        
        # Initialize FAISS index
        self.index = None
        self.metadata = []  # Store document metadata (text, source, type)
        self._load_or_create_index()
    
    def _init_embedding_model(self):
        """Initialize embedding model - prefer sentence-transformers, fallback to OpenAI"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for embeddings
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.embedding_dim = 384
                print("Using sentence-transformers for embeddings")
                return
            except Exception as e:
                print(f"Failed to load sentence-transformers: {e}")
        
        # Fallback to OpenAI embeddings
        self.use_openai_embeddings = True
        self.embedding_dim = 1536  # OpenAI text-embedding-3-small dimension
        print("Using OpenAI embeddings (requires OPENAI_API_KEY)")
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts"""
        if self.use_openai_embeddings:
            return self._get_openai_embeddings(texts)
        else:
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            return embeddings.astype('float32')
    
    def _get_openai_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings using OpenAI API (1.0+ compatible)"""
        from openai import OpenAI
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for embeddings")
        
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        embeddings = np.array([item.embedding for item in response.data], dtype=np.float32)
        return embeddings
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        if FAISS_AVAILABLE:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                try:
                    self.index = faiss.read_index(self.index_path)
                    with open(self.metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                    print(f"Loaded vector store with {len(self.metadata)} documents")
                    return
                except Exception as e:
                    print(f"Failed to load index: {e}, creating new one")
            
            # Create new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
            print("Created new vector store index")
        else:
            print("FAISS not available - vector store disabled")
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the vector store
        
        Args:
            documents: List of dicts with 'text', 'source', 'type' keys
        """
        if not FAISS_AVAILABLE:
            print("FAISS not available - cannot add documents")
            return
        
        if not documents:
            return
        
        texts = [doc['text'] for doc in documents]
        embeddings = self._get_embeddings(texts)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(documents)
        
        print(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of dicts with 'text', 'source', 'type', 'score'
        """
        if not FAISS_AVAILABLE or self.index is None or len(self.metadata) == 0:
            return []
        
        # Get query embedding
        query_embedding = self._get_embeddings([query])
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))
        
        # Format results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['score'] = float(distance)
                results.append(result)
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if not FAISS_AVAILABLE or self.index is None:
            return
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"Saved vector store: {len(self.metadata)} documents")


class A2ZIntelliBrain:
    """A2Z IntelliBrain - RAG orchestration layer"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant context from vector store
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        results = self.vector_store.search(query, k=top_k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get('source', 'Unknown')
            doc_type = result.get('type', 'document')
            text = result.get('text', '')
            
            # Extract URL from metadata if available
            metadata = result.get('metadata', {})
            url = metadata.get('url') or metadata.get('web_url')
            
            # Format with URL if available
            if url and doc_type == 'confluence_page':
                context_parts.append(f"[{doc_type}] {source}:\nLink: {url}\n{text}")
            else:
                context_parts.append(f"[{doc_type}] {source}:\n{text}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def enhance_prompt(self, user_query: str, use_rag: bool = True) -> str:
        """
        Enhance user query with retrieved context
        
        Args:
            user_query: Original user query
            use_rag: Whether to use RAG (if False, returns query as-is)
            
        Returns:
            Enhanced prompt with context
        """
        if not use_rag:
            return user_query
        
        context = self.retrieve_context(user_query)
        
        if not context:
            # No context found, return original query
            return user_query
        
        enhanced_prompt = f"""You are A2Z IntelliBrain, an AI-powered dealership co-pilot for A2Z.

Use the following context from A2Z knowledge base to answer the user's question:

{context}

User Question: {user_query}

Provide a helpful, accurate answer based on the context above. If the context doesn't contain enough information, say so and provide general guidance."""
        
        return enhanced_prompt

