"""
Confluence Knowledge Loader - Fetch and index Confluence pages
"""
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
import time


class ConfluenceLoader:
    """Load knowledge from Atlassian Confluence"""
    
    def __init__(self, confluence_url: str, username: str, api_token: str):
        """
        Initialize Confluence loader
        
        Args:
            confluence_url: Your Confluence base URL (e.g., https://yourcompany.atlassian.net/wiki)
            username: Your Confluence email/username
            api_token: Confluence API token (create at: https://id.atlassian.com/manage-profile/security/api-tokens)
        """
        self.confluence_url = confluence_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_spaces(self) -> List[Dict]:
        """Get all accessible Confluence spaces"""
        try:
            url = f"{self.confluence_url}/rest/api/space"
            response = self.session.get(url, params={'limit': 100})
            response.raise_for_status()
            spaces = response.json()['results']
            print(f"✅ Found {len(spaces)} Confluence spaces")
            return spaces
        except Exception as e:
            print(f"❌ Error fetching spaces: {e}")
            return []
    
    def get_pages_in_space(self, space_key: str, limit: int = 100) -> List[Dict]:
        """Get all pages in a Confluence space"""
        try:
            url = f"{self.confluence_url}/rest/api/content"
            params = {
                'spaceKey': space_key,
                'type': 'page',
                'limit': limit,
                'expand': 'body.storage,version,space,_links.webui,_links.tinyui'
            }
            
            all_pages = []
            start = 0
            
            while True:
                params['start'] = start
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                pages = data['results']
                all_pages.extend(pages)
                
                print(f"  Fetched {len(pages)} pages (total: {len(all_pages)})")
                
                # Check if there are more pages
                if len(pages) < limit or 'next' not in data.get('_links', {}):
                    break
                
                start += limit
                time.sleep(0.5)  # Rate limiting
            
            print(f"✅ Retrieved {len(all_pages)} pages from space '{space_key}'")
            return all_pages
            
        except Exception as e:
            print(f"❌ Error fetching pages from space {space_key}: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> Optional[Dict]:
        """Get detailed content of a specific Confluence page"""
        try:
            url = f"{self.confluence_url}/rest/api/content/{page_id}"
            params = {'expand': 'body.storage,version,space,history'}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching page {page_id}: {e}")
            return None
    
    def search_pages(self, query: str, limit: int = 50) -> List[Dict]:
        """Search Confluence pages using CQL (Confluence Query Language)"""
        try:
            url = f"{self.confluence_url}/rest/api/content/search"
            params = {
                'cql': f'type=page AND text~"{query}"',
                'limit': limit,
                'expand': 'body.storage,version,space,_links.webui,_links.tinyui'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            results = response.json()['results']
            print(f"✅ Found {len(results)} pages matching '{query}'")
            return results
            
        except Exception as e:
            print(f"❌ Error searching Confluence: {e}")
            return []
    
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from Confluence HTML content"""
        try:
            from html.parser import HTMLParser
            
            class HTMLTextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                
                def handle_data(self, data):
                    self.text_parts.append(data.strip())
                
                def get_text(self):
                    return ' '.join(filter(None, self.text_parts))
            
            parser = HTMLTextExtractor()
            parser.feed(html_content)
            return parser.get_text()
        except Exception as e:
            print(f"⚠️  Error parsing HTML: {e}")
            return html_content  # Return raw HTML as fallback
    
    def convert_pages_to_documents(self, pages: List[Dict]) -> List[Dict[str, str]]:
        """Convert Confluence pages to document format for vector store"""
        documents = []
        
        for page in pages:
            try:
                # Extract content
                body_content = page.get('body', {}).get('storage', {}).get('value', '')
                text_content = self.extract_text_from_html(body_content)
                
                # Skip empty pages
                if not text_content.strip():
                    continue
                
                # Extract metadata
                title = page.get('title', 'Untitled')
                space_name = page.get('space', {}).get('name', 'Unknown Space')
                space_key = page.get('space', {}).get('key', '')
                page_id = page.get('id', '')
                version = page.get('version', {}).get('number', 1)
                last_updated = page.get('version', {}).get('when', '')
                
                # Create web link - use the short tinyui link if available
                links = page.get('_links', {})
                if 'tinyui' in links:
                    # Use the short tinyui link (e.g., /x/H4Cblg)
                    # The base URL should not include /wiki if tinyui starts with /
                    base_url = self.confluence_url.rstrip('/')
                    tinyui = links['tinyui']
                    # tinyui is like "/x/H4Cblg", so we need to construct full URL
                    web_url = f"{base_url}{tinyui}"
                else:
                    # Fallback to old format
                    web_url = f"{self.confluence_url}/pages/viewpage.action?pageId={page_id}"
                
                # Format document
                formatted_text = f"""
                Confluence Page: {title}
                Space: {space_name} ({space_key})
                Last Updated: {last_updated}
                Link: {web_url}
                
                Content:
                {text_content}
                """
                
                document = {
                    'text': formatted_text.strip(),
                    'source': f'Confluence - {space_name} - {title}',
                    'type': 'confluence_page',
                    'metadata': {
                        'page_id': page_id,
                        'space_key': space_key,
                        'title': title,
                        'version': version,
                        'url': web_url
                    }
                }
                
                documents.append(document)
                
            except Exception as e:
                print(f"⚠️  Error converting page {page.get('title', 'Unknown')}: {e}")
                continue
        
        print(f"✅ Converted {len(documents)} Confluence pages to documents")
        return documents
    
    def load_space_knowledge(self, space_key: str, limit: int = 100) -> List[Dict[str, str]]:
        """Load all pages from a Confluence space"""
        print(f"\n📚 Loading knowledge from Confluence space: {space_key}")
        pages = self.get_pages_in_space(space_key, limit=limit)
        documents = self.convert_pages_to_documents(pages)
        return documents
    
    def load_multiple_spaces(self, space_keys: List[str], limit_per_space: int = 100) -> List[Dict[str, str]]:
        """Load pages from multiple Confluence spaces"""
        all_documents = []
        
        for space_key in space_keys:
            documents = self.load_space_knowledge(space_key, limit=limit_per_space)
            all_documents.extend(documents)
        
        print(f"\n✅ Total documents loaded from {len(space_keys)} spaces: {len(all_documents)}")
        return all_documents


def load_confluence_to_vectorstore(
    confluence_url: str,
    username: str,
    api_token: str,
    space_keys: List[str],
    vector_store
) -> int:
    """
    Load Confluence pages into the vector store
    
    Args:
        confluence_url: Confluence base URL
        username: Confluence username/email
        api_token: Confluence API token
        space_keys: List of space keys to index
        vector_store: VectorStore instance to add documents to
    
    Returns:
        Number of documents added
    """
    print("\n" + "="*70)
    print("🔄 LOADING CONFLUENCE KNOWLEDGE")
    print("="*70)
    
    # Initialize Confluence loader
    loader = ConfluenceLoader(confluence_url, username, api_token)
    
    # Load documents from specified spaces
    documents = loader.load_multiple_spaces(space_keys)
    
    if not documents:
        print("❌ No documents loaded from Confluence")
        return 0
    
    # Add to vector store
    print(f"\n📥 Adding {len(documents)} documents to vector store...")
    
    # Documents are already in the correct format (list of dicts with 'text', 'source', 'type' keys)
    vector_store.add_documents(documents)
    
    # Save the updated vector store
    vector_store.save()
    
    print(f"\n✅ Successfully added {len(documents)} Confluence pages to vector store")
    print("="*70)
    
    return len(documents)


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(__file__))
    from rag_service import VectorStore
    
    # Configuration (use environment variables in production)
    CONFLUENCE_URL = os.getenv('CONFLUENCE_URL', 'https://yourcompany.atlassian.net/wiki')
    CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME', 'your-email@company.com')
    CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN', 'your-api-token')
    SPACE_KEYS = os.getenv('CONFLUENCE_SPACES', 'SPACE1,SPACE2').split(',')
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Load Confluence knowledge
    count = load_confluence_to_vectorstore(
        confluence_url=CONFLUENCE_URL,
        username=CONFLUENCE_USERNAME,
        api_token=CONFLUENCE_API_TOKEN,
        space_keys=SPACE_KEYS,
        vector_store=vector_store
    )
    
    print(f"\n🎉 Done! Indexed {count} Confluence pages")

