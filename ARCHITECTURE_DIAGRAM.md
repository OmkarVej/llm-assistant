# A2Z IntelliBrain - System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (HTML/CSS/JavaScript)                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  • Chat Interface                                                       │ │
│  │  • Real-time messaging                                                  │ │
│  │  • Dynamic response rendering                                           │ │
│  │  • File upload (CSV for analytics)                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTP/REST API
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND API LAYER (FastAPI + Python)                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          /chat Endpoint                                 │ │
│  │  • Smart Query Detection                                                │ │
│  │  • Request Routing & Orchestration                                      │ │
│  │  • Response Formatting                                                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐            │
│  │              │              │              │              │            │
│  ▼              ▼              ▼              ▼              ▼            │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│ │Database │  │  Jira   │  │Confluence│  │   RAG   │  │ OpenAI  │         │
│ │ Query   │  │  API    │  │Knowledge │  │ Vector  │  │  API    │         │
│ │ Engine  │  │Integration│  │ Base   │  │  Store  │  │(GPT-4o) │         │
│ └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘         │
│      │            │            │            │            │              │
└──────┼────────────┼────────────┼────────────┼────────────┼──────────────┘
       │            │            │            │            │
       ▼            ▼            ▼            ▼            │
┌──────────────────────────────────────────────────────────┐│
│                    DATA SOURCES                          ││
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │   MySQL    │  │    Jira    │  │ Confluence │        ││
│  │  Database  │  │   Cloud    │  │   Cloud    │        ││
│  │            │  │            │  │            │        ││
│  │ 231 Tables │  │  Project   │  │ 389 Pages  │        ││
│  │ 309 Rels   │  │    AZ      │  │  7 Spaces  │        ││
│  └────────────┘  └────────────┘  └────────────┘        ││
│                                                           ││
│  ┌─────────────────────────────────────────────────────┐││
│  │          FAISS Vector Store                          │││
│  │  • 404 embedded documents                            │││
│  │  • Sentence-transformers (all-MiniLM-L6-v2)         │││
│  │  • 384-dimensional embeddings                        │││
│  └─────────────────────────────────────────────────────┘││
└───────────────────────────────────────────────────────────┘│
                                                             │
                                                             ▼
                                        ┌─────────────────────────────┐
                                        │    OpenAI API (External)    │
                                        │  • GPT-4o-mini LLM          │
                                        │  • Natural language          │
                                        │    generation                │
                                        └─────────────────────────────┘
```

---

## Detailed Component Architecture

### 1. Frontend Layer

```
┌─────────────────────────────────────────┐
│         User Interface (HTML)            │
├─────────────────────────────────────────┤
│  • Chat Input Box                        │
│  • Message History Display               │
│  • Real-time Response Streaming          │
│  • File Upload Widget (CSV)              │
│  • RAG Toggle                            │
└─────────────────────────────────────────┘
```

### 2. Backend API Layer (FastAPI)

```
┌─────────────────────────────────────────────────────────────┐
│                    Core API Endpoints                        │
├─────────────────────────────────────────────────────────────┤
│  POST /chat                  - Main chat interface          │
│  GET  /health                - System health check          │
│  GET  /api/conversations     - Conversation history         │
│  POST /api/database/query    - Execute SQL queries          │
│  GET  /api/jira/issue/{key}  - Get Jira issue details      │
│  POST /api/jira/search       - Execute JQL queries          │
│  POST /api/knowledge/search  - Search knowledge base        │
│  POST /api/config/update-key - Update OpenAI API key        │
└─────────────────────────────────────────────────────────────┘
```

### 3. Intelligence Layer

```
┌──────────────────────────────────────────────────────────────┐
│               Smart Query Detection & Routing                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Query Classification:                                     │
│     ├─ Greeting?          → Warm welcome response           │
│     ├─ Database Query?    → SQL Generation & Execution       │
│     ├─ Jira Ticket?       → Fetch & Summarize               │
│     ├─ JQL Query?         → Execute JQL & Format             │
│     ├─ Confluence?        → RAG Retrieval & Response         │
│     └─ General?           → OpenAI with Context              │
│                                                               │
│  2. Context Enhancement:                                      │
│     ├─ RAG Retrieval (top_k=10)                             │
│     ├─ Database Schema Injection                             │
│     ├─ Jira API Real-time Fetch                             │
│     └─ Confluence Page Retrieval                             │
│                                                               │
│  3. Response Processing:                                      │
│     ├─ SQL Marker Detection: <<<EXECUTE_QUERY: ...>>>       │
│     ├─ JQL Marker Detection: <<<EXECUTE_JQL: ...>>>         │
│     ├─ Result Formatting (Natural Language)                  │
│     └─ Error Handling (User-friendly messages)               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4. RAG (Retrieval-Augmented Generation) Pipeline

```
┌────────────────────────────────────────────────────────────┐
│                   RAG Service Pipeline                      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  User Query                                                 │
│       ↓                                                     │
│  [1] Query Embedding (sentence-transformers)               │
│       ↓                                                     │
│  [2] FAISS Vector Search (similarity search)               │
│       ↓                                                     │
│  [3] Retrieve Top-K Documents (k=10)                       │
│       ↓                                                     │
│  [4] Context Assembly                                       │
│       ├─ Confluence Pages                                   │
│       ├─ Database Schemas                                   │
│       ├─ Jira Tickets                                       │
│       └─ Documentation                                      │
│       ↓                                                     │
│  [5] Inject into System Prompt                             │
│       ↓                                                     │
│  [6] OpenAI API Call (GPT-4o-mini)                         │
│       ↓                                                     │
│  [7] Generate Response                                      │
│       ↓                                                     │
│  Formatted Output                                           │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 5. Database Query Engine

```
┌────────────────────────────────────────────────────────────┐
│              SQL Query Generation & Execution               │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Natural Language Query (e.g., "Count deals")              │
│       ↓                                                     │
│  [1] Schema Context Retrieval (from RAG)                   │
│       ├─ Table names                                        │
│       ├─ Column definitions                                 │
│       ├─ Relationships (FK constraints)                     │
│       └─ Status tables mapping                              │
│       ↓                                                     │
│  [2] AI SQL Generation (via OpenAI)                        │
│       ↓                                                     │
│  [3] Marker Detection: <<<EXECUTE_QUERY: SELECT ...>>>     │
│       ↓                                                     │
│  [4] Security Validation                                    │
│       ├─ Only SELECT allowed                                │
│       ├─ Block: DROP, DELETE, UPDATE, INSERT                │
│       └─ Prevent SQL injection                              │
│       ↓                                                     │
│  [5] Execute Query (SQLAlchemy + PyMySQL)                  │
│       ↓                                                     │
│  [6] Format Results (Natural Language)                      │
│       ├─ "There are 715 deals"                             │
│       └─ Remove SQL/JSON from output                        │
│       ↓                                                     │
│  User-Friendly Response                                     │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 6. Jira Integration

```
┌────────────────────────────────────────────────────────────┐
│                  Jira API Integration                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  A) Single Ticket Retrieval:                               │
│     User mentions: "AZ-12345"                               │
│          ↓                                                  │
│     Regex Detection: \b(AZ-\d+)\b                          │
│          ↓                                                  │
│     API Call: GET /rest/api/3/issue/{key}                  │
│          ↓                                                  │
│     Parse ADF (Atlassian Document Format)                  │
│          ↓                                                  │
│     Inject into context                                     │
│          ↓                                                  │
│     AI Summarizes                                           │
│                                                             │
│  B) JQL Query Execution:                                    │
│     User asks: "Show closed tickets"                        │
│          ↓                                                  │
│     AI Generates: <<<EXECUTE_JQL: project=AZ AND ...>>>    │
│          ↓                                                  │
│     API Call: POST /rest/api/3/search/jql                  │
│          ↓                                                  │
│     Parse Results (with pagination)                         │
│          ↓                                                  │
│     Format Output (table/list)                              │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 7. Confluence Knowledge Base

```
┌────────────────────────────────────────────────────────────┐
│             Confluence Integration Pipeline                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  [Indexing Phase - Offline]                                │
│       ↓                                                     │
│  Confluence API Call                                        │
│  GET /rest/api/content?spaceKey=X                          │
│       ↓                                                     │
│  Fetch 389 pages from 7 spaces                             │
│       ↓                                                     │
│  Extract:                                                   │
│    • Title                                                  │
│    • Body (HTML → Plain Text)                              │
│    • Metadata (space, version, dates)                      │
│    • Short URL (tinyui: /wiki/x/...)                       │
│       ↓                                                     │
│  Embed pages (sentence-transformers)                        │
│       ↓                                                     │
│  Store in FAISS Vector Store                               │
│                                                             │
│  [Query Phase - Real-time]                                 │
│       ↓                                                     │
│  User Query: "Tell me about Menu Redesign"                 │
│       ↓                                                     │
│  Vector Search → Retrieve relevant pages                   │
│       ↓                                                     │
│  Inject into context with URLs                             │
│       ↓                                                     │
│  AI generates comprehensive response                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ "Count deals"
       ▼
┌─────────────────────────────────────────┐
│  Frontend (HTML/JS)                     │
│  POST /chat {prompt: "Count deals"}    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Backend FastAPI                        │
│  /chat endpoint                         │
└──────┬──────────────────────────────────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
  ┌─────────┐  ┌──────────┐
  │   RAG   │  │ OpenAI   │
  │ Vector  │  │   API    │
  │  Store  │  │          │
  └────┬────┘  └────┬─────┘
       │            │
       │ Schema     │ "<<<EXECUTE_QUERY:
       │ Context    │  SELECT COUNT(*)
       │            │  FROM deals>>>"
       ▼            ▼
  ┌─────────────────────────┐
  │  SQL Execution Engine   │
  │  Security Check         │
  └────┬────────────────────┘
       │
       ▼
  ┌─────────────┐
  │    MySQL    │
  │  Database   │
  │  (231       │
  │   tables)   │
  └────┬────────┘
       │
       │ Result: [{total: 715}]
       ▼
  ┌─────────────────────────┐
  │  Format to Natural      │
  │  Language:              │
  │  "There are 715 deals"  │
  └────┬────────────────────┘
       │
       ▼
  ┌─────────────┐
  │  Frontend   │
  │  Display    │
  └─────────────┘
```

---

## Technology Stack

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND                               │
├──────────────────────────────────────────────────────────┤
│  • HTML5, CSS3, JavaScript (Vanilla)                     │
│  • Fetch API for async requests                          │
│  • Responsive design                                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     BACKEND                               │
├──────────────────────────────────────────────────────────┤
│  • FastAPI (Python 3.14)                                 │
│  • Uvicorn (ASGI server)                                 │
│  • CORS middleware                                        │
│  • Async/await for concurrent operations                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   AI/ML LAYER                             │
├──────────────────────────────────────────────────────────┤
│  • OpenAI API (GPT-4o-mini)                              │
│  • Sentence-Transformers (all-MiniLM-L6-v2)             │
│  • FAISS (Facebook AI Similarity Search)                 │
│  • PyTorch (ML framework)                                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    DATABASES                              │
├──────────────────────────────────────────────────────────┤
│  • MySQL 8.0 (Business data)                             │
│  • SQLite (Assistant metadata)                           │
│  • SQLAlchemy ORM                                         │
│  • PyMySQL driver                                         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                 INTEGRATIONS                              │
├──────────────────────────────────────────────────────────┤
│  • Jira Cloud API (v3)                                   │
│  • Confluence Cloud API (v2)                             │
│  • python-dotenv (env management)                        │
│  • requests library                                       │
└──────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌────────────────────────────────────────────────────────┐
│              Security Layers                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. API Security                                        │
│     ├─ CORS middleware (configured origins)            │
│     ├─ API key authentication (Jira/Confluence)        │
│     └─ Environment variable protection (.env)          │
│                                                         │
│  2. Database Security                                   │
│     ├─ Read-only SQL queries (SELECT only)            │
│     ├─ SQL injection prevention                        │
│     ├─ Keyword blacklist (DROP, DELETE, etc.)         │
│     └─ Parameterized queries (SQLAlchemy)             │
│                                                         │
│  3. Data Privacy                                        │
│     ├─ No PII logging                                  │
│     ├─ Secure credential storage                       │
│     └─ Conversation history opt-in                     │
│                                                         │
│  4. Error Handling                                      │
│     ├─ User-friendly error messages                    │
│     ├─ No SQL exposure in errors                       │
│     └─ Graceful degradation                            │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Development Environment                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐                                       │
│  │   MacOS      │                                       │
│  │  (Darwin)    │                                       │
│  └──────┬───────┘                                       │
│         │                                                │
│         ├─ Python 3.14 Virtual Environment (venv)       │
│         │                                                │
│         ├─ Backend Process                              │
│         │  └─ uvicorn backend.app:app --port 8000       │
│         │                                                │
│         ├─ Vector Store                                 │
│         │  └─ knowledge/vector_store.index              │
│         │                                                │
│         └─ Database                                      │
│            └─ MySQL (client_0000000002)                 │
│                                                          │
└─────────────────────────────────────────────────────────┘

External Services:
  • OpenAI API (api.openai.com)
  • Jira Cloud (a2zsync.atlassian.net)
  • Confluence Cloud (a2zsync.atlassian.net/wiki)
```

---

## Key Features & Capabilities

### 1. Multi-Source Intelligence

- **Database Queries**: 231 MySQL tables with intelligent SQL generation
- **Jira Integration**: Real-time ticket fetching and JQL execution
- **Confluence Knowledge**: 389 pages across 7 spaces with semantic search

### 2. Smart Query Routing

- Automatic detection of query intent
- Context-aware response generation
- Marker-based execution system

### 3. RAG-Powered Responses

- 404 documents in vector store
- Semantic similarity search
- Context injection for accurate answers

### 4. Natural Language Interface

- User-friendly responses (no SQL/JSON exposed)
- Dynamic formatting based on query type
- Helpful error messages with suggestions

### 5. Real-Time Data

- Live MySQL database access
- On-demand Jira ticket fetching
- Fresh Confluence page retrieval

---

## Performance Metrics

```
┌────────────────────────────────────────────────────┐
│             System Performance                      │
├────────────────────────────────────────────────────┤
│  • Vector Store: 404 documents                     │
│  • Database Tables: 231                            │
│  • Confluence Pages: 389                           │
│  • Jira Project: AZ (all issues accessible)       │
│  • Embedding Model: 384 dimensions                 │
│  • RAG Retrieval: top_k=10                        │
│  • Response Time: < 3 seconds (avg)               │
└────────────────────────────────────────────────────┘
```

---

## Future Enhancements (Potential)

1. **Caching Layer**: Redis for frequently accessed data
2. **Authentication**: User login and role-based access
3. **Analytics Dashboard**: Track queries, popular topics
4. **Voice Interface**: Speech-to-text integration
5. **Mobile App**: Native iOS/Android clients
6. **Multi-tenant**: Support for multiple dealerships
7. **Real-time Notifications**: WebSocket for live updates

---

_This architecture supports the A2Z IntelliBrain AI-powered dealership co-pilot, enabling intelligent conversations across databases, documentation, and project management tools._
