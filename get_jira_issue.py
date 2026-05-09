#!/usr/bin/env python3
"""
Fetch and Summarize a Specific Jira Issue
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

def get_jira_issue(issue_key):
    """Fetch a specific Jira issue"""
    try:
        url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"
        params = {
            'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,components,comment'
        }
        
        response = requests.get(
            url,
            auth=(JIRA_USERNAME, JIRA_API_TOKEN),
            headers={'Accept': 'application/json'},
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"❌ Issue {issue_key} not found")
            print("   Check:")
            print("   - Issue key is correct (case-sensitive)")
            print("   - You have permission to view this issue")
            print("   - Issue exists in your Jira instance")
            return None
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching issue: {e}")
        return None

def extract_description_text(description):
    """Extract plain text from Jira description"""
    if not description:
        return "No description provided"
    
    if isinstance(description, dict):
        # ADF format
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
        return str(description)

def summarize_issue(issue_data):
    """Summarize Jira issue in readable format"""
    if not issue_data:
        return
    
    fields = issue_data.get('fields', {})
    
    print("\n" + "="*70)
    print(f"📋 JIRA ISSUE: {issue_data.get('key', 'Unknown')}")
    print("="*70)
    
    # Basic Info
    print(f"\n📌 Summary:")
    print(f"   {fields.get('summary', 'No summary')}")
    
    print(f"\n🏷️  Type: {fields.get('issuetype', {}).get('name', 'Unknown')}")
    print(f"📊 Status: {fields.get('status', {}).get('name', 'Unknown')}")
    print(f"⚡ Priority: {fields.get('priority', {}).get('name', 'Unknown')}")
    
    # People
    assignee = fields.get('assignee')
    if assignee:
        print(f"👤 Assignee: {assignee.get('displayName', 'Unknown')}")
    else:
        print(f"👤 Assignee: Unassigned")
    
    reporter = fields.get('reporter')
    if reporter:
        print(f"📝 Reporter: {reporter.get('displayName', 'Unknown')}")
    
    # Dates
    created = fields.get('created', '')
    updated = fields.get('updated', '')
    if created:
        print(f"📅 Created: {created[:10]}")
    if updated:
        print(f"🔄 Updated: {updated[:10]}")
    
    # Resolution
    resolution = fields.get('resolution')
    if resolution:
        print(f"✅ Resolution: {resolution.get('name', 'None')}")
    
    # Labels
    labels = fields.get('labels', [])
    if labels:
        print(f"🏷️  Labels: {', '.join(labels)}")
    
    # Components
    components = [c.get('name', '') for c in fields.get('components', [])]
    if components:
        print(f"🔧 Components: {', '.join(components)}")
    
    # Description
    description = extract_description_text(fields.get('description'))
    if description and description != "No description provided":
        print(f"\n📄 Description:")
        # Truncate long descriptions
        if len(description) > 500:
            print(f"   {description[:500]}...")
            print(f"   [Truncated - full text is {len(description)} characters]")
        else:
            print(f"   {description}")
    
    # Comments
    comments_data = fields.get('comment', {}).get('comments', [])
    if comments_data:
        print(f"\n💬 Comments ({len(comments_data)} total):")
        # Show last 3 comments
        for comment in comments_data[-3:]:
            author = comment.get('author', {}).get('displayName', 'Unknown')
            created = comment.get('created', '')[:10]
            body = extract_description_text(comment.get('body'))
            
            print(f"\n   👤 {author} ({created}):")
            if len(body) > 200:
                print(f"      {body[:200]}...")
            else:
                print(f"      {body}")
    
    # Link
    print(f"\n🔗 Link: {JIRA_URL}/browse/{issue_data.get('key', '')}")
    print("="*70 + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python get_jira_issue.py ISSUE-KEY")
        print("Example: python get_jira_issue.py AZ-53118")
        sys.exit(1)
    
    issue_key = sys.argv[1].strip()
    
    print(f"\n🔍 Fetching Jira issue: {issue_key}...")
    print(f"   URL: {JIRA_URL}")
    print(f"   User: {JIRA_USERNAME}")
    
    issue_data = get_jira_issue(issue_key)
    
    if issue_data:
        summarize_issue(issue_data)
        
        # Also save to JSON for reference
        import json
        filename = f"{issue_key.replace('-', '_')}_summary.json"
        with open(filename, 'w') as f:
            json.dump(issue_data, f, indent=2)
        print(f"💾 Full details saved to: {filename}")
    else:
        print("\n❌ Could not fetch issue details")
        sys.exit(1)

if __name__ == "__main__":
    main()

