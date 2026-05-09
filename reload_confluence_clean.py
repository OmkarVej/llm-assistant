"""
Completely reload Confluence knowledge with correct short URLs
"""
import os
from dotenv import load_dotenv
from backend.rag_service import VectorStore
from backend.confluence_loader import load_confluence_to_vectorstore

# Load environment variables
load_dotenv()

# Get configuration
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME')
CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
CONFLUENCE_SPACES = os.getenv('CONFLUENCE_SPACES', '').split(',')

print("\n" + "="*70)
print("🔄 RELOADING CONFLUENCE KNOWLEDGE WITH CORRECT URLs")
print("="*70)
print(f"Confluence URL: {CONFLUENCE_URL}")
print(f"Spaces: {CONFLUENCE_SPACES}")

# Initialize vector store
vector_store = VectorStore()

# Clear existing Confluence documents BEFORE saving
print("\n🗑️  Clearing old Confluence documents...")
if hasattr(vector_store, 'metadata'):
    original_count = len(vector_store.metadata)
    
    # Keep only non-Confluence documents
    vector_store.metadata = [
        doc for doc in vector_store.metadata 
        if doc.get('type') != 'confluence_page'
    ]
    
    removed = original_count - len(vector_store.metadata)
    print(f"   Removed {removed} old Confluence documents")
    print(f"   Kept {len(vector_store.metadata)} non-Confluence documents")
    
    # Rebuild the FAISS index with remaining documents
    if vector_store.metadata:
        print(f"\n🔨 Rebuilding FAISS index...")
        texts = [doc['text'] for doc in vector_store.metadata]
        embeddings = vector_store._get_embeddings(texts)
        
        import faiss
        vector_store.index = faiss.IndexFlatL2(vector_store.embedding_dim)
        vector_store.index.add(embeddings)
        print(f"   Rebuilt index with {len(vector_store.metadata)} documents")
    else:
        # No documents left, create empty index
        import faiss
        vector_store.index = faiss.IndexFlatL2(vector_store.embedding_dim)
        print(f"   Created empty index")
    
    # Save the cleared state
    vector_store.save()
    print(f"   Saved cleared vector store")

# Reload Confluence knowledge with correct URLs
count = load_confluence_to_vectorstore(
    confluence_url=CONFLUENCE_URL,
    username=CONFLUENCE_USERNAME,
    api_token=CONFLUENCE_API_TOKEN,
    space_keys=CONFLUENCE_SPACES,
    vector_store=vector_store
)

print("\n" + "="*70)
print(f"✅ DONE! Reloaded {count} Confluence pages with correct short URLs")
print("="*70)

