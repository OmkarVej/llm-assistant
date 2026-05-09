#!/usr/bin/env python3
"""
Load Both Confluence and Jira Knowledge into Vector Store
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from confluence_loader import load_confluence_to_vectorstore
from jira_loader import load_jira_to_vectorstore
from rag_service import VectorStore

def main():
    print("\n" + "="*70)
    print("🚀 ATLASSIAN KNOWLEDGE LOADER")
    print("   Loading Confluence Pages + Jira Issues")
    print("="*70)
    
    # Initialize vector store
    print("\n📦 Initializing vector store...")
    vector_store = VectorStore()
    initial_count = len(vector_store.metadata)
    print(f"   Current documents: {initial_count}")
    
    total_loaded = 0
    
    # =================
    # CONFLUENCE
    # =================
    confluence_url = os.getenv('CONFLUENCE_URL')
    confluence_username = os.getenv('CONFLUENCE_USERNAME')
    confluence_token = os.getenv('CONFLUENCE_API_TOKEN')
    confluence_spaces = os.getenv('CONFLUENCE_SPACES', '').split(',')
    
    if all([confluence_url, confluence_username, confluence_token]) and confluence_spaces != ['']:
        print("\n" + "="*70)
        print("📚 LOADING CONFLUENCE PAGES")
        print("="*70)
        print(f"   URL: {confluence_url}")
        print(f"   Spaces: {', '.join(confluence_spaces)}")
        
        try:
            confluence_count = load_confluence_to_vectorstore(
                confluence_url=confluence_url,
                username=confluence_username,
                api_token=confluence_token,
                space_keys=confluence_spaces,
                vector_store=vector_store
            )
            total_loaded += confluence_count
            print(f"✅ Loaded {confluence_count} Confluence pages")
        except Exception as e:
            print(f"❌ Error loading Confluence: {e}")
    else:
        print("\n⚠️  Skipping Confluence (not configured)")
        print("   To enable: Set CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACES in .env")
    
    # =================
    # JIRA
    # =================
    jira_url = os.getenv('JIRA_URL')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_token = os.getenv('JIRA_API_TOKEN')
    jira_projects = os.getenv('JIRA_PROJECTS', '').split(',')
    jira_jql = os.getenv('JIRA_JQL')
    
    if all([jira_url, jira_username, jira_token]) and (jira_projects != [''] or jira_jql):
        print("\n" + "="*70)
        print("📋 LOADING JIRA ISSUES")
        print("="*70)
        print(f"   URL: {jira_url}")
        if jira_jql:
            print(f"   JQL: {jira_jql}")
        else:
            print(f"   Projects: {', '.join(jira_projects)}")
        
        try:
            jira_count = load_jira_to_vectorstore(
                jira_url=jira_url,
                username=jira_username,
                api_token=jira_token,
                project_keys=jira_projects if not jira_jql else None,
                jql=jira_jql,
                vector_store=vector_store
            )
            total_loaded += jira_count
            print(f"✅ Loaded {jira_count} Jira issues")
        except Exception as e:
            print(f"❌ Error loading Jira: {e}")
    else:
        print("\n⚠️  Skipping Jira (not configured)")
        print("   To enable: Set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN in .env")
        print("   And either JIRA_PROJECTS or JIRA_JQL")
    
    # =================
    # SUMMARY
    # =================
    print("\n" + "="*70)
    print("📊 LOADING SUMMARY")
    print("="*70)
    
    final_count = len(vector_store.metadata)
    
    print(f"\n📈 Statistics:")
    print(f"   Initial documents: {initial_count}")
    print(f"   Documents loaded: {total_loaded}")
    print(f"   Final total: {final_count}")
    print(f"   New documents: {final_count - initial_count}")
    
    if total_loaded > 0:
        print(f"\n✅ Successfully loaded {total_loaded} documents from Atlassian!")
        print("\n💡 Next steps:")
        print("   1. Restart backend: lsof -ti:8000 | xargs kill -9 && ./run_all.sh")
        print("   2. Test in UI with questions about your projects")
        print("   3. Set up a cron job to refresh daily")
    else:
        print("\n⚠️  No documents were loaded")
        print("\n📝 Configuration help:")
        print("\nFor Confluence, add to .env:")
        print("   CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki")
        print("   CONFLUENCE_USERNAME=your-email@company.com")
        print("   CONFLUENCE_API_TOKEN=your-api-token")
        print("   CONFLUENCE_SPACES=DOCS,TECH")
        print("\nFor Jira, add to .env:")
        print("   JIRA_URL=https://yourcompany.atlassian.net")
        print("   JIRA_USERNAME=your-email@company.com")
        print("   JIRA_API_TOKEN=your-api-token")
        print("   JIRA_PROJECTS=PROJ,DEV,SUPPORT")
        print("\nAPI Token: https://id.atlassian.com/manage-profile/security/api-tokens")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Loading interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

