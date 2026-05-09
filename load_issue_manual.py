#!/usr/bin/env python3
"""
Manual Jira Issue Loader - Add specific issues directly to knowledge base
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from rag_service import VectorStore

def load_issue_from_json(json_file):
    """Load a Jira issue from JSON file and add to vector store"""
    
    with open(json_file, 'r') as f:
        issue_data = json.load(f)
    
    fields = issue_data.get('fields', {})
    issue_key = issue_data.get('key', 'Unknown')
    
    # Extract information
    summary = fields.get('summary', 'No summary')
    description = fields.get('description', '')
    status = fields.get('status', {}).get('name', 'Unknown')
    priority = fields.get('priority', {}).get('name', 'Unknown')
    issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
    
    assignee = fields.get('assignee', {})
    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
    
    reporter = fields.get('reporter', {})
    reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'
    
    created = fields.get('created', '')
    updated = fields.get('updated', '')
    
    labels = fields.get('labels', [])
    components = [c.get('name', '') for c in fields.get('components', [])]
    
    # Extract description text
    if isinstance(description, dict):
        def extract_text(node):
            texts = []
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    texts.append(node.get('text', ''))
                if 'content' in node:
                    for child in node['content']:
                        texts.extend(extract_text(child))
            elif isinstance(node, list):
                for item in node:
                    texts.extend(extract_text(item))
            return texts
        
        desc_texts = extract_text(description)
        description_text = ' '.join(desc_texts)
    else:
        description_text = str(description) if description else "No description provided"
    
    # Format document
    formatted_text = f"""
Jira Issue: {issue_key} - {summary}
Type: {issue_type}
Status: {status}
Priority: {priority}
Assignee: {assignee_name}
Reporter: {reporter_name}
Created: {created}
Updated: {updated}
Labels: {', '.join(labels) if labels else 'None'}
Components: {', '.join(components) if components else 'None'}
Link: https://a2zsync.atlassian.net/browse/{issue_key}

Description:
{description_text}
"""
    
    document = {
        'text': formatted_text.strip(),
        'source': f'Jira - {issue_key} - {summary}',
        'type': 'jira_issue',
        'metadata': {
            'issue_key': issue_key,
            'issue_type': issue_type,
            'status': status,
            'priority': priority,
            'url': f'https://a2zsync.atlassian.net/browse/{issue_key}',
            'labels': labels,
            'components': components
        }
    }
    
    return document

def main():
    print("\n" + "="*70)
    print("📥 MANUAL JIRA ISSUE LOADER")
    print("="*70)
    
    # Check if JSON file exists
    json_file = 'AZ_53118_summary.json'
    if not os.path.exists(json_file):
        print(f"\n❌ File {json_file} not found")
        print("Run this first: python get_jira_issue.py AZ-53118")
        sys.exit(1)
    
    print(f"\n📄 Loading issue from: {json_file}")
    
    # Load issue
    try:
        document = load_issue_from_json(json_file)
        print(f"✅ Loaded issue: {document['metadata']['issue_key']}")
        print(f"   Type: {document['metadata']['issue_type']}")
        print(f"   Status: {document['metadata']['status']}")
    except Exception as e:
        print(f"❌ Error loading issue: {e}")
        sys.exit(1)
    
    # Initialize vector store
    print("\n📦 Initializing vector store...")
    vector_store = VectorStore()
    initial_count = len(vector_store.metadata)
    print(f"   Current documents: {initial_count}")
    
    # Add document
    print(f"\n📥 Adding issue to vector store...")
    vector_store.add_documents([document])
    vector_store.save()
    
    final_count = len(vector_store.metadata)
    print(f"\n✅ Success!")
    print(f"   Total documents: {final_count}")
    print(f"   Added: {final_count - initial_count} new documents")
    
    print("\n💡 Next steps:")
    print("   1. Restart your backend:")
    print("      lsof -ti:8000 | xargs kill -9")
    print("      cd backend && uvicorn app:app --reload --port 8000")
    print("")
    print("   2. Now you can ask: 'Summarize AZ-53118'")
    print("")
    print("=" * 70)

if __name__ == "__main__":
    main()

