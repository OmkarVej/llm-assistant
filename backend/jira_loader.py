"""
Jira Knowledge Loader - Fetch and index Jira issues
"""
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
import time


class JiraLoader:
    """Load knowledge from Atlassian Jira"""
    
    def __init__(self, jira_url: str, username: str, api_token: str):
        """
        Initialize Jira loader
        
        Args:
            jira_url: Your Jira base URL (e.g., https://yourcompany.atlassian.net)
            username: Your Jira email/username
            api_token: Jira API token (create at: https://id.atlassian.com/manage-profile/security/api-tokens)
        """
        self.jira_url = jira_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_projects(self) -> List[Dict]:
        """Get all accessible Jira projects"""
        try:
            url = f"{self.jira_url}/rest/api/3/project"
            response = self.session.get(url)
            response.raise_for_status()
            projects = response.json()
            print(f"✅ Found {len(projects)} Jira projects")
            return projects
        except Exception as e:
            print(f"❌ Error fetching projects: {e}")
            return []
    
    def get_issues_in_project(self, project_key: str, max_results: int = 100) -> List[Dict]:
        """Get issues from a Jira project"""
        try:
            url = f"{self.jira_url}/rest/api/3/search"
            
            all_issues = []
            start_at = 0
            
            while True:
                params = {
                    'jql': f'project={project_key} ORDER BY updated DESC',
                    'maxResults': max_results,
                    'startAt': start_at,
                    'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,components,comments'
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                issues = data['issues']
                all_issues.extend(issues)
                
                print(f"  Fetched {len(issues)} issues (total: {len(all_issues)})")
                
                # Check if there are more issues
                if len(all_issues) >= data['total'] or len(issues) == 0:
                    break
                
                start_at += max_results
                time.sleep(0.5)  # Rate limiting
            
            print(f"✅ Retrieved {len(all_issues)} issues from project '{project_key}'")
            return all_issues
            
        except Exception as e:
            print(f"❌ Error fetching issues from project {project_key}: {e}")
            return []
    
    def get_issue_details(self, issue_key: str) -> Optional[Dict]:
        """Get detailed information for a specific Jira issue"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            params = {
                'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,components,comments'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching issue {issue_key}: {e}")
            return None
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict]:
        """Search Jira issues using JQL (Jira Query Language)"""
        try:
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            results = response.json()['issues']
            print(f"✅ Found {len(results)} issues matching JQL: '{jql}'")
            return results
            
        except Exception as e:
            print(f"❌ Error searching Jira: {e}")
            return []
    
    def extract_description_text(self, description) -> str:
        """Extract plain text from Jira description (handles both formats)"""
        if not description:
            return "No description provided"
        
        # Jira uses Atlassian Document Format (ADF) or plain text
        if isinstance(description, dict):
            # ADF format
            return self._extract_adf_text(description)
        elif isinstance(description, str):
            # Plain text
            return description
        else:
            return str(description)
    
    def _extract_adf_text(self, adf_content: dict) -> str:
        """Extract text from Atlassian Document Format"""
        texts = []
        
        def extract_text_recursive(node):
            if isinstance(node, dict):
                # Text node
                if node.get('type') == 'text':
                    texts.append(node.get('text', ''))
                
                # Process children
                if 'content' in node:
                    for child in node['content']:
                        extract_text_recursive(child)
            elif isinstance(node, list):
                for item in node:
                    extract_text_recursive(item)
        
        extract_text_recursive(adf_content)
        return ' '.join(texts)
    
    def get_issue_comments(self, issue_key: str) -> List[Dict]:
        """Get comments for a specific issue"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/comment"
            response = self.session.get(url)
            response.raise_for_status()
            
            comments = response.json().get('comments', [])
            return comments
        except Exception as e:
            print(f"⚠️  Error fetching comments for {issue_key}: {e}")
            return []
    
    def convert_issues_to_documents(self, issues: List[Dict]) -> List[Dict[str, str]]:
        """Convert Jira issues to document format for vector store"""
        documents = []
        
        for issue in issues:
            try:
                fields = issue.get('fields', {})
                
                # Extract basic information
                issue_key = issue.get('key', 'Unknown')
                summary = fields.get('summary', 'No summary')
                description = self.extract_description_text(fields.get('description'))
                
                # Extract metadata
                status = fields.get('status', {}).get('name', 'Unknown')
                priority = fields.get('priority', {}).get('name', 'Unknown')
                issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
                
                # Assignee and reporter
                assignee = fields.get('assignee', {})
                assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                
                reporter = fields.get('reporter', {})
                reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'
                
                # Dates
                created = fields.get('created', '')
                updated = fields.get('updated', '')
                
                # Labels and components
                labels = fields.get('labels', [])
                components = [c.get('name', '') for c in fields.get('components', [])]
                
                # Resolution
                resolution = fields.get('resolution')
                resolution_name = resolution.get('name', 'Unresolved') if resolution else 'Unresolved'
                
                # Comments
                comments_data = fields.get('comment', {}).get('comments', [])
                comments_text = []
                for comment in comments_data[:5]:  # Limit to first 5 comments
                    comment_body = self.extract_description_text(comment.get('body'))
                    comment_author = comment.get('author', {}).get('displayName', 'Unknown')
                    comments_text.append(f"{comment_author}: {comment_body}")
                
                # Create web link
                web_url = f"{self.jira_url}/browse/{issue_key}"
                
                # Format document
                formatted_text = f"""
                Jira Issue: {issue_key} - {summary}
                Type: {issue_type}
                Status: {status}
                Priority: {priority}
                Resolution: {resolution_name}
                Assignee: {assignee_name}
                Reporter: {reporter_name}
                Created: {created}
                Updated: {updated}
                Labels: {', '.join(labels) if labels else 'None'}
                Components: {', '.join(components) if components else 'None'}
                Link: {web_url}
                
                Description:
                {description}
                
                {'Recent Comments:' if comments_text else ''}
                {chr(10).join(comments_text) if comments_text else ''}
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
                        'url': web_url,
                        'labels': labels,
                        'components': components
                    }
                }
                
                documents.append(document)
                
            except Exception as e:
                print(f"⚠️  Error converting issue {issue.get('key', 'Unknown')}: {e}")
                continue
        
        print(f"✅ Converted {len(documents)} Jira issues to documents")
        return documents
    
    def load_project_knowledge(self, project_key: str, max_results: int = 100) -> List[Dict[str, str]]:
        """Load all issues from a Jira project"""
        print(f"\n📋 Loading knowledge from Jira project: {project_key}")
        issues = self.get_issues_in_project(project_key, max_results=max_results)
        documents = self.convert_issues_to_documents(issues)
        return documents
    
    def load_multiple_projects(self, project_keys: List[str], max_results_per_project: int = 100) -> List[Dict[str, str]]:
        """Load issues from multiple Jira projects"""
        all_documents = []
        
        for project_key in project_keys:
            documents = self.load_project_knowledge(project_key, max_results=max_results_per_project)
            all_documents.extend(documents)
        
        print(f"\n✅ Total documents loaded from {len(project_keys)} projects: {len(all_documents)}")
        return all_documents
    
    def load_by_jql(self, jql: str, max_results: int = 100) -> List[Dict[str, str]]:
        """Load issues using custom JQL query"""
        print(f"\n🔍 Loading issues using JQL: {jql}")
        issues = self.search_issues(jql, max_results=max_results)
        documents = self.convert_issues_to_documents(issues)
        return documents


def load_jira_to_vectorstore(
    jira_url: str,
    username: str,
    api_token: str,
    project_keys: Optional[List[str]] = None,
    jql: Optional[str] = None,
    vector_store=None
) -> int:
    """
    Load Jira issues into the vector store
    
    Args:
        jira_url: Jira base URL
        username: Jira username/email
        api_token: Jira API token
        project_keys: List of project keys to index (e.g., ['PROJ', 'DEV'])
        jql: Optional JQL query to filter issues (overrides project_keys)
        vector_store: VectorStore instance to add documents to
    
    Returns:
        Number of documents added
    """
    print("\n" + "="*70)
    print("🔄 LOADING JIRA KNOWLEDGE")
    print("="*70)
    
    # Initialize Jira loader
    loader = JiraLoader(jira_url, username, api_token)
    
    # Load documents
    if jql:
        # Use JQL query
        documents = loader.load_by_jql(jql, max_results=500)
    elif project_keys:
        # Use project keys
        documents = loader.load_multiple_projects(project_keys)
    else:
        print("❌ Either project_keys or jql must be provided")
        return 0
    
    if not documents:
        print("❌ No documents loaded from Jira")
        return 0
    
    # Add to vector store
    print(f"\n📥 Adding {len(documents)} documents to vector store...")
    
    vector_store.add_documents(documents)
    
    # Save the updated vector store
    vector_store.save()
    
    print(f"\n✅ Successfully added {len(documents)} Jira issues to vector store")
    print("="*70)
    
    return len(documents)


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(__file__))
    from rag_service import VectorStore
    
    # Configuration (use environment variables in production)
    JIRA_URL = os.getenv('JIRA_URL', 'https://yourcompany.atlassian.net')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME', 'your-email@company.com')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', 'your-api-token')
    
    # Option 1: Load by project keys
    PROJECT_KEYS = os.getenv('JIRA_PROJECTS', 'PROJ,DEV').split(',')
    
    # Option 2: Load by JQL query
    # JQL = 'project in (PROJ, DEV) AND updated >= -30d'
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Load Jira knowledge
    count = load_jira_to_vectorstore(
        jira_url=JIRA_URL,
        username=JIRA_USERNAME,
        api_token=JIRA_API_TOKEN,
        project_keys=PROJECT_KEYS,
        # jql=JQL,  # Uncomment to use JQL instead
        vector_store=vector_store
    )
    
    print(f"\n🎉 Done! Indexed {count} Jira issues")

