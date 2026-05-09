import os
import yaml
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (one level up from backend/)
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
except ImportError:
    print("python-dotenv not available, skipping .env file loading")
except Exception as e:
    print(f"Could not load .env file: {e}")

# local model imports (from mini-llm repo located sibling to this backend)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from mini_llm.src.tokenizer import ByteTokenizer
    from mini_llm.src.model import MiniGPT
except Exception:
    # fallback import if structure differs
    try:
        from src.tokenizer import ByteTokenizer
        from src.model import MiniGPT
    except Exception:
        ByteTokenizer = None
        MiniGPT = None

import torch
from openai import OpenAI

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import RAG services
try:
    from rag_service import VectorStore, A2ZIntelliBrain
    from knowledge_loader import initialize_knowledge_base
    RAG_AVAILABLE = True
except Exception as e:
    print(f"RAG services not available: {e}")
    RAG_AVAILABLE = False
    A2ZIntelliBrain = None
    VectorStore = None

# Import database manager
try:
    from database import db_manager
    DB_AVAILABLE = True
except Exception as e:
    print(f"Database not available: {e}")
    DB_AVAILABLE = False
    db_manager = None

app = FastAPI(title='A2Z IntelliBrain - AI-powered dealership co-pilot')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Load config if present - check multiple possible locations
CONFIG_PATHS = [
    os.path.join(os.path.dirname(__file__), '..', 'mini_llm', 'configs', 'default.yaml'),
    os.path.join(os.path.dirname(__file__), '..', 'configs', 'default.yaml'),
    os.path.join(os.path.dirname(__file__), 'configs', 'default.yaml'),
]
cfg = {}
for CONFIG_PATH in CONFIG_PATHS:
    if os.path.exists(CONFIG_PATH):
        cfg = yaml.safe_load(open(CONFIG_PATH))
        break

# Try to prepare local model if available
LOCAL_MODEL = None
TOKENIZER = None
def init_local_model():
    global LOCAL_MODEL, TOKENIZER
    try:
        # look for checkpoint in ../checkpoints/model.pt
        ckpt_path = os.path.join(os.path.dirname(__file__), '..', 'checkpoints', 'model.pt')
        if MiniGPT is None or ByteTokenizer is None:
            return False
        TOKENIZER = ByteTokenizer()
        model_cfg = cfg.get('model', {'vocab_size':256,'block_size':128,'n_layer':2,'n_head':4,'n_embd':128,'dropout':0.1})
        LOCAL_MODEL = MiniGPT(**model_cfg)
        if os.path.exists(ckpt_path):
            LOCAL_MODEL.load_state_dict(torch.load(ckpt_path, map_location='cpu')['model_state_dict'])
        LOCAL_MODEL.eval()
        return True
    except Exception as e:
        print('Local model init failed:', e)
        return False

init_local_model()

# Initialize A2Z IntelliBrain (RAG service)
INTELLIBRAIN = None
if RAG_AVAILABLE:
    try:
        vector_store = VectorStore()
        initialize_knowledge_base(vector_store, force_reload=False)
        INTELLIBRAIN = A2ZIntelliBrain(vector_store)
        print("A2Z IntelliBrain initialized with RAG")
    except Exception as e:
        print(f"Failed to initialize IntelliBrain: {e}")
        INTELLIBRAIN = None

class ChatRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 2000  # Increased from 150 to 2000 for longer responses
    temperature: float = 0.8
    top_k: int = 50
    use_local: bool = False
    use_rag: bool = True  # Enable RAG by default
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    save_to_db: bool = True  # Save conversation to database

@app.get('/health')
async def health():
    db_status = 'connected' if (DB_AVAILABLE and db_manager and db_manager.engine) else 'disconnected'
    api_key = os.environ.get('OPENAI_API_KEY', '')
    return {
        'status': 'ok',
        'local_model_loaded': LOCAL_MODEL is not None,
        'rag_available': INTELLIBRAIN is not None,
        'vector_store_documents': len(INTELLIBRAIN.vector_store.metadata) if INTELLIBRAIN else 0,
        'database_status': db_status,
        'openai_key_loaded': len(api_key) > 0,
        'openai_key_preview': f"{api_key[:20]}...{api_key[-10:]}" if len(api_key) > 30 else "Not set",
        'smart_detection_test': 'desking' in 'how many leads are in desking?'.lower()
    }

@app.post('/api/config/update-api-key')
async def update_api_key(request: dict):
    """Update OpenAI API key dynamically without restart"""
    try:
        new_key = request.get('api_key', '').strip()
        
        if not new_key:
            raise HTTPException(status_code=400, detail='API key is required')
        
        if not new_key.startswith('sk-'):
            raise HTTPException(status_code=400, detail='Invalid API key format')
        
        # Update environment variable
        os.environ['OPENAI_API_KEY'] = new_key
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            updated = False
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('OPENAI_API_KEY='):
                        f.write(f'OPENAI_API_KEY={new_key}\n')
                        updated = True
                    else:
                        f.write(line)
                
                if not updated:
                    f.write(f'\nOPENAI_API_KEY={new_key}\n')
        
        # Update .env.env.backup file
        backup_path = os.path.join(os.path.dirname(__file__), '..', '.env.env.backup')
        if os.path.exists(backup_path):
            with open(backup_path, 'r') as f:
                lines = f.readlines()
            
            updated = False
            with open(backup_path, 'w') as f:
                for line in lines:
                    if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
                        f.write(f'OPENAI_API_KEY={new_key}\n')
                        updated = True
                    else:
                        f.write(line)
                
                if not updated:
                    f.write(f'\nOPENAI_API_KEY={new_key}\n')
        
        # Test the new key
        try:
            from openai import OpenAI
            client = OpenAI(api_key=new_key)
            # Make a minimal test request
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': 'test'}],
                max_tokens=1
            )
            key_valid = True
            test_message = 'API key validated successfully'
        except Exception as e:
            key_valid = False
            test_message = f'API key set but validation failed: {str(e)}'
        
        return {
            'success': True,
            'message': 'API key updated in all locations',
            'files_updated': ['.env', '.env.env.backup', 'environment variable'],
            'key_preview': f"{new_key[:20]}...{new_key[-10:]}",
            'key_valid': key_valid,
            'test_message': test_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error updating API key: {str(e)}')

async def execute_database_query_internal(query: str) -> dict:
    """Internal function to execute database queries"""
    if not DB_AVAILABLE or not db_manager:
        return {'success': False, 'error': 'Database not available', 'data': []}
    
    # Security: Only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return {'success': False, 'error': 'Only SELECT queries allowed', 'data': []}
    
    # Block dangerous keywords (check as whole words, not substrings)
    import re
    dangerous = ['\\bDROP\\b', '\\bDELETE\\b(?!D_AT)', '\\bUPDATE\\b(?!D_AT)', '\\bINSERT\\b', '\\bALTER\\b', '\\bCREATE\\b', '\\bTRUNCATE\\b']
    for pattern in dangerous:
        if re.search(pattern, query_upper):
            return {'success': False, 'error': 'Dangerous keyword detected', 'data': []}
    
    session = db_manager.get_session()
    try:
        from sqlalchemy import text
        result = session.execute(text(query))
        rows = [dict(row._mapping) for row in result]
        return {'success': True, 'row_count': len(rows), 'data': rows}
    except Exception as e:
        return {'success': False, 'error': str(e), 'data': []}
    finally:
        session.close()


async def execute_jira_query_internal(jql: str) -> dict:
    """Internal function to execute Jira JQL queries"""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            return {'success': False, 'error': 'Jira not configured', 'data': [], 'total': 0}
        
        # Use Jira API v3 POST endpoint (the new way)
        url = f"{jira_url}/rest/api/3/search/jql"
        
        # First request to get initial results
        payload = {
            'jql': jql,
            'maxResults': 50,  # Get up to 50 results
            'fields': ['summary', 'status', 'priority', 'issuetype', 'assignee', 'created', 'updated', 'sprint']
        }
        
        response = requests.post(
            url,
            auth=(jira_username, jira_api_token),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return {'success': False, 'error': f'Jira API error: {response.status_code} - {response.text[:200]}', 'data': [], 'total': 0}
        
        data = response.json()
        issues = data.get('issues', [])
        is_last = data.get('isLast', True)
        
        # Format results
        results = []
        for issue in issues:
            fields = issue.get('fields', {})
            
            # Extract sprint information if available
            sprint_info = 'No Sprint'
            if fields.get('sprint'):
                # Sprint can be an array or a single object
                sprint_data = fields.get('sprint')
                if isinstance(sprint_data, list) and len(sprint_data) > 0:
                    sprint_info = sprint_data[-1].get('name', 'No Sprint')
                elif isinstance(sprint_data, dict):
                    sprint_info = sprint_data.get('name', 'No Sprint')
            
            results.append({
                'key': issue.get('key'),
                'summary': fields.get('summary', 'N/A'),
                'status': fields.get('status', {}).get('name', 'N/A'),
                'priority': fields.get('priority', {}).get('name', 'N/A'),
                'type': fields.get('issuetype', {}).get('name', 'N/A'),
                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                'sprint': sprint_info,
                'created': fields.get('created', 'N/A'),
                'updated': fields.get('updated', 'N/A')
            })
        
        # For counts, we need to paginate to get accurate total
        # Or estimate based on whether there's more data
        total = len(results)
        if not is_last:
            total = f"{total}+"  # Indicate there are more
        
        return {'success': True, 'total': total, 'returned': len(results), 'data': results, 'has_more': not is_last}
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'data': [], 'total': 0}


@app.post('/chat')
async def chat(req: ChatRequest):
    # Smart query detection for common patterns
    import re
    prompt_lower = req.prompt.lower()
    
    # Debug logging
    print(f"\n🔍 Processing query: '{req.prompt}'")
    print(f"   Lowercase: '{prompt_lower}'")
    
    count_words = ['how many', 'count', 'total', 'number of']
    has_count = any(word in prompt_lower for word in count_words)
    
    # Detect desking queries directly
    if 'desking' in prompt_lower and has_count:
        print("   ✅ DESKING SMART DETECTION TRIGGERED!")
        sql = "SELECT COUNT(*) as total FROM payment_calculations WHERE lead_for_desking = 1 AND deleted_at IS NULL"
        result = await execute_database_query_internal(sql)
        
        if result['success'] and result['row_count'] > 0:
            total = result['data'][0]['total']
            print(f"   ✅ Query executed: {total} leads in desking")
            return {
                'source': 'smart_detection',
                'response': f"There are a total of {total} leads in desking.",
                'rag_used': False,
                'context': None,
                'model': 'direct_query',
                'conversation_id': None,
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }
    
    # Detect staff user queries directly
    if ('staff' in prompt_lower or 'employee' in prompt_lower) and has_count:
        print("   ✅ STAFF SMART DETECTION TRIGGERED!")
        sql = "SELECT COUNT(*) as total FROM users WHERE is_staff = 1 AND deleted_at IS NULL"
        result = await execute_database_query_internal(sql)
        print(f"   📊 Query result: {result}")
        
        if result['success'] and result['row_count'] > 0:
            total = result['data'][0]['total']
            print(f"   ✅ Query executed: {total} staff users")
            return {
                'source': 'smart_detection',
                'response': f"There are a total of {total} staff users.",
                'rag_used': False,
                'context': None,
                'model': 'direct_query',
                'conversation_id': None,
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }
        else:
            print(f"   ❌ Query failed or no results: {result}")
    
    # Detect pending deals queries - redirect to incomplete
    if 'pending' in prompt_lower and 'deal' in prompt_lower and has_count:
        print("   ✅ PENDING DEALS DETECTION - Redirecting to incomplete")
        sql = "SELECT COUNT(*) as total FROM deals WHERE complete = 0 AND deleted_at IS NULL"
        result = await execute_database_query_internal(sql)
        
        if result['success'] and result['row_count'] > 0:
            total = result['data'][0]['total']
            print(f"   ✅ Query executed: {total} incomplete deals")
            return {
                'source': 'smart_detection',
                'response': f"Note: The deals table doesn't have a 'pending' status. However, there are {total} incomplete deals (deals that aren't finished yet). Is this what you're looking for?",
                'rag_used': False,
                'context': None,
                'model': 'direct_query',
                'conversation_id': None,
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }
    
    # Detect incomplete deals queries
    if ('incomplete' in prompt_lower or 'in progress' in prompt_lower or 'unfinished' in prompt_lower) and 'deal' in prompt_lower and has_count:
        print("   ✅ INCOMPLETE DEALS SMART DETECTION TRIGGERED!")
        sql = "SELECT COUNT(*) as total FROM deals WHERE complete = 0 AND deleted_at IS NULL"
        result = await execute_database_query_internal(sql)
        
        if result['success'] and result['row_count'] > 0:
            total = result['data'][0]['total']
            print(f"   ✅ Query executed: {total} incomplete deals")
            return {
                'source': 'smart_detection',
                'response': f"There are a total of {total} incomplete deals.",
                'rag_used': False,
                'context': None,
                'model': 'direct_query',
                'conversation_id': None,
                'usage': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            }
    
    print("   ℹ️  Continuing to OpenAI...")
    
    # Enhance prompt with RAG if available and enabled
    enhanced_prompt = req.prompt
    retrieved_context = None
    
    # Check if user is asking about a Jira ticket
    import re
    jira_matches = re.findall(r'\b(AZ-\d+)\b', req.prompt, re.IGNORECASE)
    jira_context = None
    
    if jira_matches and req.use_rag:
        # Fetch Jira issue details for each mentioned ticket
        jira_issues = []
        for issue_key in jira_matches:
            try:
                import requests
                from dotenv import load_dotenv
                load_dotenv()
                
                jira_url = os.getenv('JIRA_URL')
                jira_username = os.getenv('JIRA_USERNAME')
                jira_api_token = os.getenv('JIRA_API_TOKEN')
                
                if all([jira_url, jira_username, jira_api_token]):
                    url = f"{jira_url}/rest/api/3/issue/{issue_key.upper()}"
                    params = {
                        'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,components'
                    }
                    
                    response = requests.get(
                        url,
                        auth=(jira_username, jira_api_token),
                        headers={'Accept': 'application/json'},
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        issue_data = response.json()
                        fields = issue_data.get('fields', {})
                        
                        # Extract description text
                        desc = fields.get('description', {})
                        if isinstance(desc, dict) and desc.get('type') == 'doc':
                            # Extract text from ADF format
                            desc_text = []
                            for content in desc.get('content', []):
                                if content.get('type') == 'paragraph':
                                    for item in content.get('content', []):
                                        if item.get('type') == 'text':
                                            desc_text.append(item.get('text', ''))
                            description = ' '.join(desc_text)
                        else:
                            description = str(desc) if desc else 'No description'
                        
                        # Format issue info
                        jira_info = f"""
Jira Issue: {issue_key.upper()}
Summary: {fields.get('summary', 'N/A')}
Type: {fields.get('issuetype', {}).get('name', 'N/A')}
Status: {fields.get('status', {}).get('name', 'N/A')}
Priority: {fields.get('priority', {}).get('name', 'N/A')}
Created: {fields.get('created', 'N/A')}
Updated: {fields.get('updated', 'N/A')}
Reporter: {fields.get('reporter', {}).get('displayName', 'N/A')}
Assignee: {fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'}
Description: {description}
Link: {jira_url}/browse/{issue_key.upper()}
"""
                        jira_issues.append(jira_info)
            except Exception as e:
                print(f"Failed to fetch Jira {issue_key}: {e}")
        
        if jira_issues:
            jira_context = "\n\n---\n\n".join(jira_issues)
    
    if req.use_rag and INTELLIBRAIN is not None:
        enhanced_prompt = INTELLIBRAIN.enhance_prompt(req.prompt, use_rag=True)
        retrieved_context = INTELLIBRAIN.retrieve_context(req.prompt, top_k=10)
        
        # Add Jira context if available
        if jira_context:
            if retrieved_context:
                retrieved_context = f"{jira_context}\n\n---\n\n{retrieved_context}"
            else:
                retrieved_context = jira_context
    
    # Check if this is a database query request (expanded keywords for any table)
    query_keywords = ['count', 'how many', 'show', 'list', 'total', 'sum', 'average', 'find', 'search', 'get', 'display']
    # Don't limit to specific data keywords - let RAG handle all tables
    is_likely_query = any(kw in req.prompt.lower() for kw in query_keywords)
    
    # choose local model if requested and available
    if req.use_local and LOCAL_MODEL is not None and TOKENIZER is not None:
        try:
            ids = TOKENIZER.encode(enhanced_prompt)
            import torch
            idx = torch.tensor([ids], dtype=torch.long)
            out = LOCAL_MODEL.generate(idx, max_new_tokens=req.max_new_tokens, temperature=req.temperature, top_k=req.top_k)
            text = TOKENIZER.decode(out[0].tolist())
            
            # Save to database if enabled
            conversation_id = None
            if req.save_to_db and DB_AVAILABLE and db_manager:
                conversation_id = db_manager.save_conversation(
                    prompt=req.prompt,
                    response=text,
                    source='local',
                    user_id=req.user_id,
                    session_id=req.session_id,
                    rag_used=req.use_rag and INTELLIBRAIN is not None,
                    model='local_minigpt',
                    tokens_used=None,
                    meta_data={'context_used': retrieved_context is not None}
                )
            
            return {
                'source': 'local',
                'response': text,
                'rag_used': req.use_rag and INTELLIBRAIN is not None,
                'context': retrieved_context if retrieved_context else None,
                'conversation_id': conversation_id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Local model error: {e}')
    
    # otherwise use OpenAI if API key present
    api_key = os.environ.get('OPENAI_API_KEY') or cfg.get('openai_api_key') or cfg.get('OPENAI_API_KEY')
    if not api_key:
        error_msg = 'No OPENAI_API_KEY provided and local model unavailable.\n'
        error_msg += 'To fix this:\n'
        error_msg += '1. Set OPENAI_API_KEY environment variable: export OPENAI_API_KEY="your-key"\n'
        error_msg += '2. Or add "openai_api_key: your-key" to mini_llm/configs/default.yaml\n'
        error_msg += '3. Or train a local model: cd mini_llm && python src/train.py --config configs/default.yaml\n'
        error_msg += f'   (Local model status: {"available" if LOCAL_MODEL is not None else "not available"})'
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        # Use new OpenAI 1.0+ API
        client = OpenAI(api_key=api_key)
        
        # Use enhanced prompt with RAG context
        system_message = '''You are A2Z IntelliBrain, an AI-powered dealership co-pilot for A2Z.

        CONVERSATION RULES:
        - For greetings ("hi", "hello", "hey"), respond warmly and ask how you can help
        - For Confluence questions, use the context provided from the knowledge base to give detailed, accurate answers
        - For general questions, provide helpful answers using your knowledge
        - For specific Jira tickets (AZ-xxxxx), I will fetch them automatically
        - For Jira QUERIES (how many, closed tickets, etc.), use JQL execution system below
        - For database queries (count, how many, show, list, total), use SQL execution system below
        
        CONFLUENCE KNOWLEDGE:
        - When context from Confluence pages is provided, USE IT to answer the question
        - Provide detailed information from the Confluence pages
        - Include relevant links and page titles
        - If multiple pages are relevant, mention all of them
        - Be comprehensive - don't give generic responses when you have specific information

JIRA QUERY INTELLIGENCE:
Project: AZ (all Jira tickets are in the AZ project)

Common JQL patterns:
- Count closed tickets: project = AZ AND status = Closed
- Tickets by team: project = AZ AND labels = "team-name"
- Recent tickets: project = AZ AND created >= -30d
- Assigned to someone: project = AZ AND assignee = "email@example.com"
- By sprint: project = AZ AND sprint = "Sprint 16"
- By status: project = AZ AND status IN (Open, "In Progress", Closed)
- User's tickets in sprint: project = AZ AND assignee = "email" AND sprint = "Sprint 16"

IMPORTANT JQL RULES:
- For assignee, try to match the name to an email (e.g., "ashutosh" → search for ashutosh's email)
- Sprint names are usually "Sprint X" where X is the number
- If you need to find user's email, ask OR use display name: assignee in (ashutosh)

JQL EXECUTION (for Jira data questions):
- Response format: ONLY "<<<EXECUTE_JQL: your_jql_here>>>"
- Do NOT explain, do NOT show JQL - just the marker
- I will execute and show results
- For queries about specific people, try: assignee in (firstname) OR use display name matching

DATABASE INTELLIGENCE:
You have access to a COMPLETE A2Z database with 231 tables and full schema details in your knowledge base.

CRITICAL RULES FOR ALL TABLES:
1. The knowledge base contains COMPLETE schema for ALL 231 tables with ALL column names
2. You receive schema context from the knowledge base with ACTUAL table and column names
3. If retrieved context shows a table/column, USE IT immediately and confidently
4. Generate queries using EXACT table and column names from the retrieved context
5. NEVER make up or guess table/column names - use ONLY what's in the context
6. The knowledge base has the authoritative schema - TRUST IT completely

UNDERSTANDING STATUS/RELATIONSHIP TABLES:
- Many tables have status_id columns that reference separate status tables
- Pattern: table_name → table_name_statuses (e.g., credit_apps → credit_app_statuses)
- When user asks for "approved", "pending", "active", "closed" etc., look for status relationships
- JOIN with status table to filter by status NAME, not just ID
- Use WHERE clauses with status conditions when user specifies status

SMART QUERY GENERATION:
- "how many X" → SELECT COUNT(*) as total FROM X
- "how many approved X" → Look for X_statuses table, JOIN and filter by status name
- "how many pending X" → JOIN with X_statuses WHERE status_name = 'Pending'
- "list X by status" → JOIN with X_statuses, GROUP BY status name
- Always use column aliases for counts: COUNT(*) as total_X

SPECIAL BUSINESS TERMS:
- "desking" / "leads in desking" → Query payment_calculations table WHERE lead_for_desking = 1
  Example: "how many leads in desking" → SELECT COUNT(*) FROM payment_calculations WHERE lead_for_desking = 1 AND deleted_at IS NULL
- payment_calculations.lead_for_desking: 0 = not in desking, 1 = in desking
- "staff users" / "staff members" / "employees" → Query users table WHERE is_staff = 1
  Example: "how many staff users" → SELECT COUNT(*) FROM users WHERE is_staff = 1 AND deleted_at IS NULL
- users.is_staff: 1 = staff/employee, 0 = regular user/customer
- Always check deleted_at IS NULL for active records

SQL EXECUTION (for database questions):
- When you see schema info in context, generate the query immediately
- Response format: ONLY "<<<EXECUTE_QUERY: your_sql_here>>>"
- Do NOT explain, do NOT show SQL - just the marker
- I will execute and show results in natural language

EXAMPLES OF CORRECT BEHAVIOR:
✅ User: "hi" → Response: "Hello! I'm A2Z IntelliBrain, your dealership co-pilot. How can I assist you today?"
✅ User: "summarize AZ-12345" → I fetch it automatically → Provide clear summary
✅ User: "how many closed tickets in amazon team" → Response: "<<<EXECUTE_JQL: project = AZ AND status = Closed AND labels = "amazon">>>"
✅ User: "Count deals" → Response: "<<<EXECUTE_QUERY: SELECT COUNT(*) as total FROM deals>>>"
✅ User: "Count credit apps" → Response: "<<<EXECUTE_QUERY: SELECT COUNT(*) as total FROM credit_apps>>>"
✅ User: "how many approved credit apps" → Response: "<<<EXECUTE_QUERY: SELECT COUNT(*) as total FROM credit_apps ca JOIN credit_app_statuses cas ON ca.status_id = cas.id WHERE cas.name = 'Decision'>>>"
✅ User: "how many leads are in desking" → Response: "<<<EXECUTE_QUERY: SELECT COUNT(*) as total FROM payment_calculations WHERE lead_for_desking = 1 AND deleted_at IS NULL>>>"
✅ User: "how many staff users" → Response: "<<<EXECUTE_QUERY: SELECT COUNT(*) as total FROM users WHERE is_staff = 1 AND deleted_at IS NULL>>>"
✅ User: "how many pending deals" → If deals_statuses exists → JOIN and filter by 'Pending'

CRITICAL: For ANY database question, you MUST respond with ONLY the marker. Do NOT say "I encountered an issue" or any error message. If unsure about the query, make your best attempt using the schema from context.

The knowledge base has ALL 231 tables. Use it for EVERY table - no exceptions!'''
        
        if retrieved_context:
            system_message += '\n\n=== CONTEXT FROM KNOWLEDGE BASE ===\n\n'
            system_message += retrieved_context
            system_message += '\n\n=== END OF CONTEXT ===\n\n'
            system_message += '''IMPORTANT: The context above contains information from your knowledge base (Confluence pages, database schemas, etc.).
            
            When answering questions:
            - If the context contains Confluence pages, provide detailed information from those pages
            - Include page titles and links from the context
            - Quote specific information from the context
            - DO NOT give generic responses like "I don't have specific details" when context is provided
            - BE COMPREHENSIVE and use all relevant information from the context
            
            For database queries and Jira queries, use the marker system described above.'''
        
        model_name = os.environ.get('OPENAI_MODEL') or cfg.get('OPENAI_MODEL') or 'gpt-4o-mini'
        
        # Call OpenAI chat completion using new API
        # Use req.prompt directly since context is in system message
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': req.prompt}
            ],
            max_tokens=req.max_new_tokens,
            temperature=req.temperature
        )
        
        text = response.choices[0].message.content
        
        # Debug: Log what OpenAI returned
        print(f"\n🤖 OpenAI returned: '{text[:100]}'")
        
        # Replace generic error messages with friendly ones
        if "I encountered an issue" in text or "Please try rephrasing" in text:
            print("   ✅ Replacing with friendly message!")
            text = "Buddy... that question is too heavy. I'm a mini-LLM, not ChatGPT-Ultra. Try rephrasing!"
        
        # Check if AI wants to execute a JQL query (Jira)
        if '<<<EXECUTE_JQL:' in text:
            import re
            # Extract JQL query
            match = re.search(r'<<<EXECUTE_JQL:\s*(.+?)>>>', text, re.DOTALL)
            if match:
                jql_query = match.group(1).strip()
                
                # Execute the JQL query
                result = await execute_jira_query_internal(jql_query)
                
                # Remove the execute marker from response
                text = re.sub(r'<<<EXECUTE_JQL:.+?>>>', '', text, flags=re.DOTALL).strip()
                
                # Format results in clean, simple way
                if result['success']:
                    total = result['total']
                    returned = result['returned']
                    data = result['data']
                    has_more = result.get('has_more', False)
                    
                    if total == 0:
                        text = "No tickets found matching that criteria."
                    elif 'how many' in req.prompt.lower() or 'count' in req.prompt.lower():
                        # User wants count
                        text = f"Total Tickets: {total}"
                        if returned > 0 and returned <= 5:
                            # Show a few examples
                            text += "\n\nSample tickets:\n"
                            for i, ticket in enumerate(data[:5], 1):
                                text += f"\n{i}. {ticket['key']}: {ticket['summary']}\n"
                                text += f"   Status: {ticket['status']}, Priority: {ticket['priority']}\n"
                                if ticket.get('sprint') and ticket['sprint'] != 'No Sprint':
                                    text += f"   Sprint: {ticket['sprint']}\n"
                    else:
                        # User wants list
                        text = f"Found {total} ticket(s)"
                        if returned > 0:
                            text += "\n\n"
                            for i, ticket in enumerate(data[:10], 1):  # Show max 10
                                text += f"{i}. {ticket['key']}: {ticket['summary']}\n"
                                text += f"   Status: {ticket['status']}, Priority: {ticket['priority']}, Type: {ticket['type']}\n"
                                text += f"   Assignee: {ticket['assignee']}\n"
                                if ticket.get('sprint') and ticket['sprint'] != 'No Sprint':
                                    text += f"   Sprint: {ticket['sprint']}\n"
                                text += "\n"
                            # Check if there are more tickets (handle both int and str total)
                            if has_more or (isinstance(total, int) and total > 10):
                                if isinstance(total, int):
                                    text += f"... and {total - 10} more tickets"
                                else:
                                    text += f"... and more tickets available"
                else:
                    text = f"I encountered an issue querying Jira: {result['error']}"
        
        # Check if AI wants to execute a SQL query (Database)
        elif '<<<EXECUTE_QUERY:' in text:
            import re
            # Extract SQL query
            match = re.search(r'<<<EXECUTE_QUERY:\s*(.+?)>>>', text, re.DOTALL)
            if match:
                sql_query = match.group(1).strip()
                # Remove markdown code blocks if present
                sql_query = re.sub(r'^```sql\s*', '', sql_query)
                sql_query = re.sub(r'\s*```$', '', sql_query)
                
                # Execute the query
                result = await execute_database_query_internal(sql_query)
                
                # Remove the execute marker and any explanation from response
                text = re.sub(r'<<<EXECUTE_QUERY:.+?>>>', '', text, flags=re.DOTALL).strip()
                
                # Format results in clean, simple way
                if result['success']:
                    if result['row_count'] == 1 and len(result['data']) > 0:
                        # Single result - show clean format
                        first_row = result['data'][0]
                        if len(first_row) == 1:
                            # Single column result (e.g., count) - make it natural
                            key = list(first_row.keys())[0]
                            value = list(first_row.values())[0]
                            
                            # Extract the entity name from key or prompt
                            entity = key.replace('total_', '').replace('total', '').replace('_', ' ').strip()
                            if not entity:
                                # Try to extract from prompt
                                prompt_lower = req.prompt.lower()
                                if 'credit app' in prompt_lower:
                                    entity = 'credit apps' if 'approved' in prompt_lower else 'credit apps'
                                elif 'deal' in prompt_lower:
                                    entity = 'deals'
                                elif 'customer' in prompt_lower:
                                    entity = 'customers'
                                elif 'vehicle' in prompt_lower:
                                    entity = 'vehicles'
                                else:
                                    entity = 'records'
                            
                            # Create natural sentence
                            if 'how many' in req.prompt.lower() or 'count' in req.prompt.lower():
                                # Check if the query has conditions (approved, pending, etc.)
                                if any(word in req.prompt.lower() for word in ['approved', 'pending', 'open', 'closed', 'active']):
                                    status_word = next((w for w in ['approved', 'pending', 'open', 'closed', 'active'] if w in req.prompt.lower()), '')
                                    text = f"There are a total of {value} {status_word} {entity}."
                                else:
                                    text = f"There are a total of {value} {entity}."
                            else:
                                text = f"Total {entity.title()}: {value}"
                        else:
                            # Multiple columns - show as key: value pairs
                            parts = []
                            for key, value in first_row.items():
                                label = key.replace('_', ' ').title()
                                parts.append(f"{label}: {value}")
                            text = "\n".join(parts)
                    elif result['row_count'] > 1:
                        # Multiple results - show as table
                        text = "Results:\n\n"
                        for i, row in enumerate(result['data'][:10], 1):  # Show max 10
                            text += f"{i}. "
                            parts = []
                            for key, value in row.items():
                                label = key.replace('_', ' ').title()
                                parts.append(f"{label}: {value}")
                            text += ", ".join(parts) + "\n"
                        if result['row_count'] > 10:
                            text += f"\n... and {result['row_count'] - 10} more"
                    else:
                        text = "No results found."
                else:
                    # Smart error messages - don't reveal limited capabilities
                    error_msg = result['error'].lower()
                    
                    if 'unknown column' in error_msg or 'no such column' in error_msg:
                        text = "I couldn't find that specific information in the database. Could you rephrase your question?"
                    elif "doesn't exist" in error_msg or 'no such table' in error_msg:
                        text = "I don't have access to that specific data in the system."
                    elif 'syntax error' in error_msg:
                        text = "I had trouble understanding that request. Could you rephrase it?"
                    elif 'permission denied' in error_msg or 'access denied' in error_msg:
                        text = "I don't have permission to access that information."
                    elif 'timeout' in error_msg:
                        text = "That query is taking too long. Could you try asking for less data or be more specific?"
                    else:
                        text = "Buddy... that question is too heavy. I'm a mini-LLM, not ChatGPT-Ultra. Try rephrasing!"
        
        # Save to database if enabled
        conversation_id = None
        if req.save_to_db and DB_AVAILABLE and db_manager:
            try:
                conversation_id = db_manager.save_conversation(
                    prompt=req.prompt,
                    response=text,
                    source='openai',
                    user_id=req.user_id,
                    session_id=req.session_id,
                    rag_used=req.use_rag and INTELLIBRAIN is not None,
                    model=model_name,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    meta_data={'context_used': retrieved_context is not None}
                )
            except Exception as save_error:
                # Don't fail the request if saving fails - just log it
                print(f"Warning: Could not save conversation: {save_error}")
                # Conversation saving failed but response is still valid
        
        return {
            'source': 'openai',
            'response': text,
            'rag_used': req.use_rag and INTELLIBRAIN is not None,
            'context': retrieved_context if retrieved_context else None,
            'model': model_name,
            'conversation_id': conversation_id,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                'completion_tokens': response.usage.completion_tokens if response.usage else None,
                'total_tokens': response.usage.total_tokens if response.usage else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'OpenAI error: {str(e)}')


# A2Z API Integration Endpoints

@app.get('/api/compliance/rules')
async def get_compliance_rules():
    """Get compliance rules from knowledge base"""
    if not INTELLIBRAIN:
        raise HTTPException(status_code=503, detail='RAG service not available')
    
    results = INTELLIBRAIN.vector_store.search('compliance rules regulations', k=5)
    compliance_docs = [r for r in results if r.get('type') == 'compliance']
    
    return {
        'rules': [{'text': doc['text'], 'source': doc['source']} for doc in compliance_docs]
    }


@app.get('/api/lending/sample-payload')
async def get_lending_sample_payload():
    """Get sample lending payload from knowledge base"""
    if not INTELLIBRAIN:
        raise HTTPException(status_code=503, detail='RAG service not available')
    
    results = INTELLIBRAIN.vector_store.search('lending approved decision payload', k=3)
    payload_docs = [r for r in results if r.get('type') == 'api_payload']
    
    return {
        'payloads': [{'text': doc['text'], 'source': doc['source']} for doc in payload_docs]
    }


@app.get('/api/search')
async def search_knowledge_base(query: str, top_k: int = 5):
    """Search the A2Z knowledge base"""
    if not INTELLIBRAIN:
        raise HTTPException(status_code=503, detail='RAG service not available')
    
    results = INTELLIBRAIN.vector_store.search(query, k=top_k)
    
    return {
        'query': query,
        'results': [
            {
                'text': r['text'],
                'source': r['source'],
                'type': r.get('type', 'unknown'),
                'score': r.get('score', 0)
            }
            for r in results
        ]
    }


# Database endpoints

@app.get('/api/conversations/history')
async def get_conversation_history(user_id: Optional[str] = None, 
                                  session_id: Optional[str] = None, 
                                  limit: int = 10):
    """Get conversation history from database"""
    if not DB_AVAILABLE or not db_manager:
        raise HTTPException(status_code=503, detail='Database not available')
    
    history = db_manager.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )
    
    return {
        'conversations': history,
        'count': len(history)
    }


@app.get('/api/stats/conversations/count')
async def count_conversations():
    """Count total conversations in database"""
    if not DB_AVAILABLE or not db_manager:
        raise HTTPException(status_code=503, detail='Database not available')
    
    session = db_manager.get_session()
    try:
        from database import Conversation
        count = session.query(Conversation).count()
        return {
            'total_conversations': count,
            'message': f'There are {count} conversations stored in the database'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error counting conversations: {str(e)}')
    finally:
        session.close()


@app.get('/api/stats/database')
async def get_database_stats():
    """Get database statistics"""
    if not DB_AVAILABLE or not db_manager:
        raise HTTPException(status_code=503, detail='Database not available')
    
    session = db_manager.get_session()
    try:
        from database import Conversation, KnowledgeDocument
        
        total_conversations = session.query(Conversation).count()
        total_knowledge_docs = session.query(KnowledgeDocument).count()
        
        # Get RAG usage stats
        rag_used_count = session.query(Conversation).filter(Conversation.rag_used == 1).count()
        
        return {
            'total_conversations': total_conversations,
            'total_knowledge_documents': total_knowledge_docs,
            'rag_usage': {
                'used': rag_used_count,
                'percentage': round((rag_used_count / total_conversations * 100), 2) if total_conversations > 0 else 0
            },
            'note': 'This database stores AI assistant conversations and knowledge documents. It does NOT contain business deals data.'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting stats: {str(e)}')
    finally:
        session.close()


class QueryRequest(BaseModel):
    """SQL query request"""
    query: str
    params: Optional[dict] = None


@app.post('/api/database/query')
async def execute_query(request: QueryRequest):
    """Execute a read-only SQL query on the database"""
    if not DB_AVAILABLE or not db_manager:
        raise HTTPException(status_code=503, detail='Database not available')
    
    # Security: Only allow SELECT queries
    query_upper = request.query.strip().upper()
    if not query_upper.startswith('SELECT'):
        raise HTTPException(status_code=400, detail='Only SELECT queries are allowed')
    
    # Block dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(status_code=400, detail=f'Keyword {keyword} is not allowed')
    
    session = db_manager.get_session()
    try:
        from sqlalchemy import text
        
        # Execute query with parameters
        result = session.execute(text(request.query), request.params or {})
        
        # Convert to list of dicts
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        return {
            'success': True,
            'row_count': len(rows),
            'data': rows
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'row_count': 0,
            'data': []
        }
    finally:
        session.close()


# Jira Integration Endpoints

@app.get('/api/jira/issue/{issue_key}')
async def get_jira_issue(issue_key: str):
    """Get a specific Jira issue by key"""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise HTTPException(status_code=503, detail='Jira not configured')
        
        url = f"{jira_url}/rest/api/3/issue/{issue_key}"
        params = {
            'fields': 'summary,description,status,priority,issuetype,assignee,reporter,created,updated,resolution,labels,components'
        }
        
        response = requests.get(
            url,
            auth=(jira_username, jira_api_token),
            headers={'Accept': 'application/json'},
            params=params,
            timeout=10
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f'Issue {issue_key} not found')
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f'Error fetching Jira issue: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/jira/search')
async def search_jira_issues(query: str, max_results: int = 10):
    """Search Jira issues using JQL or text query"""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise HTTPException(status_code=503, detail='Jira not configured')
        
        # If query looks like JQL, use it directly, otherwise search in summary/description
        if 'project' in query.lower() or '=' in query:
            jql = query
        else:
            jql = f'text ~ "{query}" ORDER BY updated DESC'
        
        url = f"{jira_url}/rest/api/3/search"
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'summary,description,status,priority,issuetype,assignee,updated'
        }
        
        response = requests.get(
            url,
            auth=(jira_username, jira_api_token),
            headers={'Accept': 'application/json'},
            params=params,
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            'total': data.get('total', 0),
            'issues': data.get('issues', [])
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f'Error searching Jira: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
