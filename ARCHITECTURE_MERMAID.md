# A2Z IntelliBrain - Mermaid Architecture Diagrams

## System Overview Diagram

```mermaid
graph TB
    User[👤 User] --> Frontend[🖥️ Frontend<br/>HTML/CSS/JS]
    Frontend --> API[⚡ FastAPI Backend<br/>Port 8000]
    
    API --> RAG[🧠 RAG Engine<br/>FAISS Vector Store]
    API --> DB[💾 Database Engine<br/>SQL Generator]
    API --> Jira[🎫 Jira Integration<br/>REST API v3]
    API --> Conf[📚 Confluence<br/>Knowledge Base]
    API --> OpenAI[🤖 OpenAI API<br/>GPT-4o-mini]
    
    RAG --> VectorStore[(📊 Vector Store<br/>404 documents)]
    DB --> MySQL[(🗄️ MySQL<br/>231 tables)]
    Jira --> JiraCloud[☁️ Jira Cloud<br/>Project AZ]
    Conf --> ConfCloud[☁️ Confluence Cloud<br/>389 pages]
    
    style User fill:#e1f5fe
    style Frontend fill:#fff3e0
    style API fill:#f3e5f5
    style OpenAI fill:#e8f5e9
    style RAG fill:#fce4ec
    style DB fill:#fff9c4
    style Jira fill:#e0f2f1
    style Conf fill:#f1f8e9
```

## Data Flow Diagram - Database Query

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant F as 🖥️ Frontend
    participant A as ⚡ API
    participant R as 🧠 RAG
    participant O as 🤖 OpenAI
    participant D as 💾 MySQL
    
    U->>F: "Count deals"
    F->>A: POST /chat
    A->>R: Retrieve schema context
    R-->>A: Table definitions
    A->>O: Generate SQL with context
    O-->>A: <<<EXECUTE_QUERY: SELECT COUNT(*)...>>>
    A->>A: Extract & validate SQL
    A->>D: Execute query
    D-->>A: Result: 715
    A->>A: Format: "There are 715 deals"
    A-->>F: Natural language response
    F-->>U: Display "There are 715 deals"
```

## Data Flow Diagram - Confluence Search

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant F as 🖥️ Frontend
    participant A as ⚡ API
    participant R as 🧠 RAG
    participant V as 📊 Vector Store
    participant O as 🤖 OpenAI
    
    U->>F: "Tell me about Menu Redesign"
    F->>A: POST /chat {use_rag: true}
    A->>R: Search knowledge base
    R->>V: Vector similarity search
    V-->>R: Top 10 relevant pages
    R-->>A: Confluence context + URLs
    A->>O: Generate response with context
    O-->>A: Detailed explanation
    A-->>F: Response with page links
    F-->>U: Display comprehensive answer
```

## Data Flow Diagram - Jira Integration

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant F as 🖥️ Frontend
    participant A as ⚡ API
    participant J as 🎫 Jira API
    participant O as 🤖 OpenAI
    
    U->>F: "Summarize AZ-12345"
    F->>A: POST /chat
    A->>A: Detect ticket pattern (AZ-\d+)
    A->>J: GET /rest/api/3/issue/AZ-12345
    J-->>A: Issue details + description
    A->>A: Parse ADF format
    A->>O: Summarize with context
    O-->>A: Summary text
    A-->>F: Formatted summary + link
    F-->>U: Display ticket summary
```

## Component Architecture

```mermaid
graph LR
    subgraph Frontend
        UI[User Interface]
        Chat[Chat Component]
        Upload[File Upload]
    end
    
    subgraph Backend
        API[FastAPI Router]
        Smart[Smart Detection]
        
        subgraph Intelligence
            RAG[RAG Service]
            DBEngine[DB Query Engine]
            JiraInt[Jira Integration]
            ConfInt[Confluence Loader]
        end
        
        subgraph Security
            Auth[Authentication]
            Valid[SQL Validation]
            CORS[CORS Middleware]
        end
    end
    
    subgraph DataLayer
        MySQL[(MySQL DB)]
        Vector[(Vector Store)]
        SQLite[(SQLite)]
    end
    
    subgraph External
        OpenAI[OpenAI API]
        JiraAPI[Jira Cloud]
        ConfAPI[Confluence Cloud]
    end
    
    UI --> API
    API --> Smart
    Smart --> RAG
    Smart --> DBEngine
    Smart --> JiraInt
    Smart --> ConfInt
    
    RAG --> Vector
    DBEngine --> MySQL
    JiraInt --> JiraAPI
    ConfInt --> ConfAPI
    
    API --> OpenAI
    API --> SQLite
    
    API --> Auth
    API --> Valid
    API --> CORS
```

## RAG Pipeline

```mermaid
flowchart TD
    Start[User Query] --> Embed[Embed Query<br/>sentence-transformers]
    Embed --> Search[FAISS Vector Search<br/>Similarity matching]
    Search --> Retrieve[Retrieve Top-K=10<br/>Documents]
    Retrieve --> Check{Document Type?}
    
    Check -->|Confluence| ConfDoc[Confluence Pages<br/>+ URLs]
    Check -->|Schema| SchemaDoc[Database Schemas<br/>+ Relationships]
    Check -->|Jira| JiraDoc[Jira Tickets<br/>+ Context]
    
    ConfDoc --> Assemble[Assemble Context]
    SchemaDoc --> Assemble
    JiraDoc --> Assemble
    
    Assemble --> Inject[Inject into<br/>System Prompt]
    Inject --> OpenAI[OpenAI API Call<br/>GPT-4o-mini]
    OpenAI --> Response[Generate Response]
    Response --> Format[Format Output]
    Format --> End[Return to User]
    
    style Start fill:#e3f2fd
    style OpenAI fill:#e8f5e9
    style End fill:#fff9c4
```

## Security Flow

```mermaid
flowchart TD
    Query[SQL Query Request] --> Check1{Type = SELECT?}
    Check1 -->|No| Reject1[❌ Reject:<br/>Only SELECT allowed]
    Check1 -->|Yes| Check2{Dangerous Keywords?}
    
    Check2 -->|Yes| Reject2[❌ Reject:<br/>DROP/DELETE/UPDATE forbidden]
    Check2 -->|No| Check3{Valid Syntax?}
    
    Check3 -->|No| Reject3[❌ Reject:<br/>Invalid SQL]
    Check3 -->|Yes| Param[Parameterize Query<br/>SQLAlchemy]
    
    Param --> Execute[Execute via<br/>MySQL Connection]
    Execute --> Result[Return Results]
    
    Reject1 --> Error[User-Friendly<br/>Error Message]
    Reject2 --> Error
    Reject3 --> Error
    
    style Result fill:#e8f5e9
    style Error fill:#ffebee
```

## Technology Stack

```mermaid
graph TB
    subgraph Frontend_Stack[Frontend Stack]
        HTML[HTML5]
        CSS[CSS3]
        JS[JavaScript ES6+]
    end
    
    subgraph Backend_Stack[Backend Stack]
        FastAPI[FastAPI]
        Python[Python 3.14]
        Uvicorn[Uvicorn ASGI]
    end
    
    subgraph AI_ML[AI/ML Stack]
        OpenAI_API[OpenAI API]
        SentenceT[Sentence Transformers]
        FAISS[FAISS]
        PyTorch[PyTorch]
    end
    
    subgraph Database_Stack[Database Stack]
        MySQL_DB[MySQL 8.0]
        SQLite_DB[SQLite]
        SQLAlchemy[SQLAlchemy ORM]
        PyMySQL[PyMySQL]
    end
    
    subgraph Integration_Stack[Integrations]
        Jira_API[Jira API v3]
        Conf_API[Confluence API v2]
        Requests[Requests Library]
    end
    
    Frontend_Stack --> Backend_Stack
    Backend_Stack --> AI_ML
    Backend_Stack --> Database_Stack
    Backend_Stack --> Integration_Stack
```

## Deployment View

```mermaid
graph TB
    subgraph Development[Development Environment - MacOS]
        subgraph Python_Env[Python 3.14 venv]
            Backend[Backend Process<br/>uvicorn:8000]
            VStore[Vector Store<br/>knowledge/]
        end
        
        subgraph Local_DB[Local Database]
            MySQL_Local[MySQL<br/>client_0000000002]
            SQLite_Local[SQLite<br/>assistant.db]
        end
        
        Frontend_Local[Frontend<br/>HTML Files]
    end
    
    subgraph External_Services[External Services]
        OpenAI_Service[OpenAI API<br/>api.openai.com]
        Jira_Service[Jira Cloud<br/>a2zsync.atlassian.net]
        Conf_Service[Confluence Cloud<br/>a2zsync.atlassian.net/wiki]
    end
    
    Frontend_Local --> Backend
    Backend --> VStore
    Backend --> MySQL_Local
    Backend --> SQLite_Local
    Backend --> OpenAI_Service
    Backend --> Jira_Service
    Backend --> Conf_Service
    
    style Development fill:#e3f2fd
    style External_Services fill:#f3e5f5
```

## System State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle: System Start
    
    Idle --> Processing: User Query Received
    
    Processing --> RAGRetrieval: use_rag = true
    Processing --> DirectQuery: use_rag = false
    
    RAGRetrieval --> ContextEnhancement: Vector Search Complete
    DirectQuery --> ContextEnhancement: No RAG needed
    
    ContextEnhancement --> DetectIntent: Context Ready
    
    DetectIntent --> Greeting: Pattern: hi/hello
    DetectIntent --> DatabaseQuery: Pattern: count/how many
    DetectIntent --> JiraTicket: Pattern: AZ-\d+
    DetectIntent --> JQLQuery: Jira search keywords
    DetectIntent --> ConfluenceQuery: Confluence keywords
    DetectIntent --> GeneralQuery: Other
    
    Greeting --> Response: Warm welcome
    DatabaseQuery --> SQLGeneration: Generate SQL
    SQLGeneration --> SQLExecution: Validate & Execute
    SQLExecution --> Response: Format results
    
    JiraTicket --> FetchJira: API call
    FetchJira --> Response: Parse & summarize
    
    JQLQuery --> ExecuteJQL: POST /search/jql
    ExecuteJQL --> Response: Format list
    
    ConfluenceQuery --> Response: Use RAG context
    GeneralQuery --> Response: OpenAI generation
    
    Response --> Idle: Return to user
    
    Idle --> [*]: System Stop
```

## Error Handling Flow

```mermaid
flowchart TD
    Request[API Request] --> Try{Try Execute}
    
    Try -->|Success| Return[Return Response]
    Try -->|Error| Detect{Error Type?}
    
    Detect -->|Rate Limit| RateLimit[OpenAI Quota Error]
    Detect -->|DB Error| DBError[Database Error]
    Detect -->|Network| NetworkError[Network/Timeout Error]
    Detect -->|Invalid Query| InvalidQuery[Invalid Request]
    Detect -->|Other| GenericError[Generic Error]
    
    RateLimit --> Friendly1[User Message:<br/>'Buddy... that question is too heavy']
    DBError --> Friendly2[User Message:<br/>'Having trouble accessing the database']
    NetworkError --> Friendly3[User Message:<br/>'Connection timed out']
    InvalidQuery --> Friendly4[User Message:<br/>'Could you rephrase that?']
    GenericError --> Friendly5[User Message:<br/>'Something went wrong']
    
    Friendly1 --> Log[Log Error Details]
    Friendly2 --> Log
    Friendly3 --> Log
    Friendly4 --> Log
    Friendly5 --> Log
    
    Log --> Return
    
    style Return fill:#e8f5e9
    style Friendly1 fill:#fff9c4
    style Friendly2 fill:#fff9c4
    style Friendly3 fill:#fff9c4
    style Friendly4 fill:#fff9c4
    style Friendly5 fill:#fff9c4
```

---

## How to Use These Diagrams

### For Presentations:
1. Copy the Mermaid code blocks into https://mermaid.live
2. Export as PNG/SVG for slides
3. Or use Mermaid plugins in PowerPoint/Keynote

### For Documentation:
- GitHub automatically renders Mermaid diagrams
- Confluence supports Mermaid with plugins
- Use markdown preview tools that support Mermaid

### For Hackathon:
- Use the "System Overview" for high-level explanation
- Use "Data Flow" diagrams to show query processing
- Use "Component Architecture" to show technical depth

---

*These diagrams visualize the complete A2Z IntelliBrain architecture, from user interface to data sources.*

