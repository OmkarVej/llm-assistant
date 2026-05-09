#!/usr/bin/env python3
import os
import sys

# Set environment variables directly
confluence_url = 'https://a2zsync.atlassian.net/wiki'
username = 'prashanth.vanama@a2zsync.com'
api_token = 'ATATT3xFfGF0MeOX85N6mGEHI4UtsIerUnO9sw1fVVMQofNHeGwyRwCy6yGkTj62mGQNrw_Q4zEpPZFMOISD3EvCEoICq1s2s3H13TDUj9U3F7rcf7POP81mtUUFa3AbVGCYSrlkc9bPEvWm3ZcEJJi3i9UGayxXv-lyYJRG069yq6tEc-r88JI=22F0092F'
spaces = 'ASCS,AT,API,DW,DEVOPS,CLI,Product & Engineering Ops'

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from confluence_loader import ConfluenceLoader
from rag_service import VectorStore

print("=" * 70)
print("🔄 RELOADING CONFLUENCE DATA")
print("=" * 70)

# Initialize
print("\n📦 Initializing...")
store = VectorStore()
loader = ConfluenceLoader(confluence_url, username, api_token)

# Get current doc count
all_docs_before = store.search("", k=1000)
print(f"   Current documents in store: {len(all_docs_before)}")

# Get spaces
space_list = [s.strip() for s in spaces.split(',') if s.strip()]
print(f"\n2️⃣ Loading from {len(space_list)} spaces: {space_list}")

total_pages = 0
all_new_docs = []

for space_key in space_list:
    try:
        print(f"\n   📁 Space: {space_key}")
        pages = loader.get_pages_in_space(space_key, limit=100)
        print(f"      Fetched {len(pages)} pages")
        
        if pages:
            # Convert to documents
            docs = loader.convert_pages_to_documents(pages)
            print(f"      Converted to {len(docs)} documents")
            
            # Check first document structure
            if docs:
                first_doc = docs[0]
                metadata = first_doc.get('metadata', {})
                print(f"      ✓ Sample doc:")
                print(f"        - Title: {metadata.get('title', 'N/A')}")
                print(f"        - Source: {metadata.get('source', 'N/A')}")
                url = metadata.get('web_url', 'N/A')
                print(f"        - URL: {url[:70] + '...' if len(url) > 70 else url}")
            
            all_new_docs.extend(docs)
            total_pages += len(pages)
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print(f"3️⃣ Adding {len(all_new_docs)} documents to vector store...")

if all_new_docs:
    try:
        store.add_documents(all_new_docs)
        print(f"   ✅ Successfully added!")
    except Exception as e:
        print(f"   ❌ Error adding documents: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print(f"✅ RELOAD COMPLETE!")
print(f"   Total pages loaded: {total_pages}")
print(f"   Total documents added: {len(all_new_docs)}")
print("=" * 70)

# Verify
print("\n4️⃣ Verifying...")
test_docs = store.search("Confluence", k=3)
print(f"   Found {len(test_docs)} documents when searching 'Confluence'")

if test_docs:
    print("\n   Sample documents:")
    for i, doc in enumerate(test_docs[:3], 1):
        metadata = doc.get('metadata', {})
        print(f"\n   {i}. {metadata.get('title', 'Unknown')}")
        print(f"      Source: {metadata.get('source', 'N/A')}")
        url = metadata.get('web_url', 'N/A')
        print(f"      URL: {url[:70] + '...' if len(url) > 70 else url}")

print("\n✅ Done!\n")

