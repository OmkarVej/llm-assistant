#!/usr/bin/env python3
"""
Script to load Confluence pages into the RAG vector store
"""
import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("    Or manually set environment variables")

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from rag_service import VectorStore
from confluence_loader import load_confluence_to_vectorstore


def main():
    print("\n" + "="*70)
    print("🚀 CONFLUENCE TO VECTOR STORE LOADER")
    print("="*70)
    
    # Get configuration from environment variables
    confluence_url = os.getenv('CONFLUENCE_URL')
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    spaces = os.getenv('CONFLUENCE_SPACES', '').split(',')
    
    # Validate configuration
    if not confluence_url:
        print("\n❌ Error: CONFLUENCE_URL not set")
        print("\nPlease set the following environment variables:")
        print("  export CONFLUENCE_URL='https://yourcompany.atlassian.net/wiki'")
        print("  export CONFLUENCE_USERNAME='your-email@company.com'")
        print("  export CONFLUENCE_API_TOKEN='your-api-token'")
        print("  export CONFLUENCE_SPACES='SPACE1,SPACE2,SPACE3'")
        print("\nOr add them to your .env file")
        return 1
    
    if not username or not api_token:
        print("\n❌ Error: CONFLUENCE_USERNAME or CONFLUENCE_API_TOKEN not set")
        print("\nCreate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens")
        return 1
    
    if not spaces or spaces == ['']:
        print("\n❌ Error: CONFLUENCE_SPACES not set")
        print("\nSpecify space keys separated by commas, e.g.: SPACE1,SPACE2")
        return 1
    
    print(f"\n📋 Configuration:")
    print(f"   Confluence URL: {confluence_url}")
    print(f"   Username: {username}")
    print(f"   Spaces: {', '.join(spaces)}")
    print()
    
    # Confirm before proceeding
    response = input("Proceed with loading Confluence pages? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return 0
    
    # Initialize vector store
    print("\n📦 Initializing vector store...")
    vector_store = VectorStore()
    
    # Load Confluence knowledge
    count = load_confluence_to_vectorstore(
        confluence_url=confluence_url,
        username=username,
        api_token=api_token,
        space_keys=spaces,
        vector_store=vector_store
    )
    
    if count > 0:
        print(f"\n✅ SUCCESS! Indexed {count} Confluence pages")
        print("\nTo use the knowledge:")
        print("  1. Restart your backend server")
        print("  2. Ask questions using the chat API with 'use_rag: true'")
        print("  3. The system will automatically search Confluence pages")
        return 0
    else:
        print("\n❌ No pages were indexed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

