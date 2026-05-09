#!/usr/bin/env python3
"""
Alternative Jira Loader - Using Direct Issue Fetch
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from jira_loader import JiraLoader
from rag_service import VectorStore

# Configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

print("\n" + "="*70)
print("🔄 LOADING JIRA KNOWLEDGE - ALTERNATIVE METHOD")
print("="*70)
print(f"\n📋 Configuration:")
print(f"   Jira URL: {JIRA_URL}")
print(f"   Username: {JIRA_USERNAME}")

# Initialize Jira loader
loader = JiraLoader(JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN)

# Initialize vector store
print("\n📦 Initializing vector store...")
vector_store = VectorStore()
initial_count = len(vector_store.metadata)
print(f"   Current documents in vector store: {initial_count}")

# Try loading with different JQL queries
jql_queries = [
    'key = AZ-53118',  # Specific issue
    'project = AZ AND updated >= -90d ORDER BY updated DESC',  # Recent issues
    'project = AZ ORDER BY created DESC',  # All issues ordered by creation
]

all_documents = []

for jql in jql_queries:
    print(f"\n🔍 Trying JQL: {jql}")
    try:
        documents = loader.load_by_jql(jql, max_results=500)
        if documents:
            all_documents.extend(documents)
            print(f"✅ Loaded {len(documents)} issues with this query")
            break  # Stop if we found issues
        else:
            print(f"⚠️  No issues found with this query")
    except Exception as e:
        print(f"❌ Error with query: {e}")
        continue

if all_documents:
    print(f"\n📥 Adding {len(all_documents)} documents to vector store...")
    vector_store.add_documents(all_documents)
    vector_store.save()
    
    final_count = len(vector_store.metadata)
    print(f"\n✅ Success! Indexed {len(all_documents)} Jira issues")
    print(f"📊 Total documents in vector store: {final_count}")
    print(f"📈 Added: {final_count - initial_count} new documents")
    
    print("\n💡 Tip: Restart your backend to use the updated knowledge:")
    print("   lsof -ti:8000 | xargs kill -9")
    print("   cd backend && uvicorn app:app --reload --port 8000")
else:
    print("\n❌ Could not load any Jira issues")
    print("\n⚠️  The API endpoint might be deprecated or restricted.")
    print("\n💡 Alternative: Use the direct API endpoints I added:")
    print("   GET /api/jira/issue/AZ-53118")
    print("   GET /api/jira/search?query=project=AZ")

