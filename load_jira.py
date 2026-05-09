#!/usr/bin/env python3
"""
Load Jira Issues into Knowledge Base
This script loads Jira issues without affecting Confluence or Database data
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.jira_loader import load_jira_to_vectorstore
from backend.rag_service import VectorStore

def main():
    print("\n" + "="*70)
    print("🚀 JIRA TO VECTOR STORE LOADER")
    print("="*70)
    
    # Get Jira configuration from environment
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_api_token = os.getenv('JIRA_API_TOKEN')
    jira_projects = os.getenv('JIRA_PROJECTS', 'AZ')
    
    if not all([jira_url, jira_username, jira_api_token]):
        print("❌ Error: Missing Jira credentials in .env file")
        print("   Required: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        return 1
    
    print(f"\n📋 Configuration:")
    print(f"   Jira URL: {jira_url}")
    print(f"   Username: {jira_username}")
    print(f"   Projects: {jira_projects}")
    
    # Get user confirmation
    response = input("\nProceed with loading Jira issues? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Aborted by user")
        return 1
    
    # Initialize vector store (this will load existing knowledge)
    print("\n📦 Initializing vector store...")
    vector_store = VectorStore()
    
    initial_count = len(vector_store.metadata)
    print(f"✅ Current knowledge base has {initial_count} documents")
    
    # Count existing Jira docs
    existing_jira = len([d for d in vector_store.metadata if d.get('type') == 'jira_issue'])
    print(f"   Existing Jira issues: {existing_jira}")
    
    # Parse project keys
    project_keys = [p.strip() for p in jira_projects.split(',')]
    
    # Load Jira knowledge
    print("\n" + "="*70)
    print("🔄 LOADING JIRA ISSUES")
    print("="*70)
    
    count = load_jira_to_vectorstore(
        jira_url=jira_url,
        username=jira_username,
        api_token=jira_api_token,
        project_keys=project_keys,
        vector_store=vector_store
    )
    
    final_count = len(vector_store.metadata)
    new_jira = len([d for d in vector_store.metadata if d.get('type') == 'jira_issue'])
    
    print("\n" + "="*70)
    print("✅ SUCCESS! Jira issues loaded")
    print("="*70)
    print(f"   Before: {initial_count} total documents ({existing_jira} Jira)")
    print(f"   After: {final_count} total documents ({new_jira} Jira)")
    print(f"   Added: {count} new Jira issues")
    print("\n💡 To use the knowledge:")
    print("   1. Restart your backend server")
    print("   2. Ask questions about Jira issues")
    print("   3. The system will automatically search Jira data")
    print("\n✨ Confluence and Database data remain unchanged!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
