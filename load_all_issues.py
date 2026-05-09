#!/usr/bin/env python3
"""
Load multiple Jira issues into knowledge base
"""
import os
import sys
import json
import glob
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from rag_service import VectorStore

def extract_text_from_description(description):
    """Extract plain text from Jira description"""
    if not description:
        return "No description provided"
    
    if isinstance(description, dict):
        texts = []
        def extract_text_recursive(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    texts.append(node.get('text', ''))
                if 'content' in node:
                    for child in node['content']:
                        extract_text_recursive(child)
            elif isinstance(node, list):
                for item in node:
                    extract_text_recursive(item)
        
        extract_text_recursive(description)
        return ' '.join(texts)
    else:
        return str(description) if description else "No description provided"

def load_issue_from_json(json_file):
    """Load a Jira issue from JSON file and convert to document"""
    
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
    
    created = fields.get('created', '')[:10]
    updated = fields.get('updated', '')[:10]
    
    labels = fields.get('labels', [])
    components = [c.get('name', '') for c in fields.get('components', [])]
    
    description_text = extract_text_from_description(description)
    
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
    
    return document, issue_key

def main():
    print("\n" + "="*70)
    print("📥 BULK JIRA ISSUE LOADER")
    print("="*70)
    
    # Find all JSON summary files
    json_files = glob.glob('AZ_*_summary.json')
    
    if not json_files:
        print("\n❌ No Jira summary JSON files found")
        print("Run: python get_jira_issue.py AZ-XXXXX")
        sys.exit(1)
    
    print(f"\n📄 Found {len(json_files)} issue files:")
    for f in json_files:
        print(f"   • {f}")
    
    # Load issues
    documents = []
    loaded_keys = []
    
    for json_file in json_files:
        try:
            document, issue_key = load_issue_from_json(json_file)
            documents.append(document)
            loaded_keys.append(issue_key)
            print(f"✅ Loaded: {issue_key}")
        except Exception as e:
            print(f"❌ Error loading {json_file}: {e}")
    
    if not documents:
        print("\n❌ No documents loaded")
        sys.exit(1)
    
    # Initialize vector store
    print(f"\n📦 Initializing vector store...")
    vector_store = VectorStore()
    initial_count = len(vector_store.metadata)
    print(f"   Current documents: {initial_count}")
    
    # Add documents
    print(f"\n📥 Adding {len(documents)} issues to vector store...")
    vector_store.add_documents(documents)
    vector_store.save()
    
    final_count = len(vector_store.metadata)
    print(f"\n✅ Success!")
    print(f"   Issues loaded: {', '.join(loaded_keys)}")
    print(f"   Total documents: {final_count}")
    print(f"   Added: {final_count - initial_count} new documents")
    
    print("\n💡 Next steps:")
    print("   1. Restart your backend:")
    print("      lsof -ti:8000 | xargs kill -9")
    print("      cd backend && uvicorn app:app --reload --port 8000")
    print("")
    print(f"   2. Now you can ask about: {', '.join(loaded_keys)}")
    print("")
    print("=" * 70)

if __name__ == "__main__":
    main()

