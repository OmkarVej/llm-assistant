# 1. Project Overview

## Executive Summary

**Project Name:** Conversational AI Co-Pilot for A2Z  
**Purpose:** Reduce the time employees spend finding answers across disconnected enterprise systems.

Employees currently spend hours searching across multiple tools, switching between **Jira**, **Confluence**, and **database interfaces** with separate logins and query patterns. Simple business questions often take **5–10 minutes**, knowledge is scattered and hard to locate, and teams rely heavily on technical users for SQL/data retrieval—creating bottlenecks and slowing decisions.

This project delivers a **unified conversational AI assistant** that provides natural language access to:

- **MySQL database** (natural language querying across **231 tables**)
- **Jira** (sprint tracking and ticket intelligence)
- **Confluence documentation** (RAG-based retrieval over **793 indexed documents**)
- **Business terminology and dealership workflows** (e.g., “desking”, “approved credit apps”, “active deals”)

Example queries:

- “How many leads are in desking?”
- “Show Ashutosh tickets in sprint 16”
- “Summarize Jira AZ-54628”
- “Explain DynamoDB optimization strategy”

Expected business impact:

- **~90% faster information retrieval**
- **Single conversational interface** for multi-system discovery
- **Reduced dependency on SQL expertise**
- **Improved organizational knowledge accessibility**

---

# 2. Functional Specifications (MAIN FOCUS)

The assistant turns a user’s natural-language request into **safe, scoped retrieval actions** across database/Jira/Confluence and returns an **answer-first, evidence-backed** response. Each module below includes objective, I/O, validation, failure handling, and edge cases.

## 2.1 User Request Intake

- **Objective**: Accept requests, capture session context, and standardize inputs for downstream processing.
- **Inputs**: Prompt text; user identity/role; session id; optional tenant/client scope; prior-turn context.
- **Internal processing**: Normalize text; detect explicit routing hints (“from Jira…”); pre-extract obvious identifiers (ticket keys, dates).
- **Validation logic**: Input size limits; rate limiting; baseline policy filtering (secrets, bulk export patterns).
- **Output format**: `RequestEnvelope { text, user, session, scope?, extracted_entities?, timestamp }`.
- **Failure handling**: Return user-safe errors without internal stack traces; suggest corrective actions.
- **Edge cases**: Multi-question prompts → split into sub-requests; missing scope → mark for clarification.

## 2.2 Natural Language Understanding (NLU)

- **Objective**: Determine intent(s) and extract entities required for DB/Jira/Confluence execution.
- **Inputs**: `RequestEnvelope`; prior context; business/domain lexicon.
- **Internal processing**:
  - **Intent classification** (may be multi-intent): DB query, Jira intelligence, Confluence RAG, or orchestrated multi-source.
  - **Entity extraction**: Jira keys (`AZ-54628`), sprint (“sprint 16”), assignees (“Ashutosh”), dates/ranges, business terms.
  - Confidence scoring; create an execution plan (parallel vs sequential).
- **Validation logic**: Required-entity checks (e.g., Jira key for ticket summary); low confidence triggers clarification instead of guessing.
- **Output format**: `Plan { intents[], entities, confidence, sources[], order, constraints }`.
- **Failure handling**: Ask one targeted clarification question when ambiguity is material.
- **Edge cases**: Name ambiguity for assignees; “Explain … strategy” defaults to Confluence/RAG.

## 2.3 Intent Classification + Routing (Multi-Agent Orchestration)

- **Objective**: Route work to the correct connector(s) and coordinate execution across sources.
- **Inputs**: `Plan`; connector availability; latency budgets.
- **Internal processing**:
  - Decide source(s): DB vs Jira vs Confluence vs combination.
  - Execute in parallel when independent; sequential when dependent (e.g., DB result → follow-up).
  - Merge and deduplicate results; resolve conflicts via precedence rules and explicit disclosure.
- **Validation logic**: Connector-level permissions; global timeout budgets; enforce “least data necessary” outputs.
- **Output format**: `OrchestrationResult { partial_results[], warnings?, citations[] }`.
- **Failure handling**: Partial answers with clear disclosure (what failed, why, and next steps).
- **Edge cases**: Conflicting source answers; connector rate limiting; source timeouts.

## 2.4 Database Query Generation + SQL Validation

- **Objective**: Convert business questions into safe, read-only SQL and return explainable results.
- **Inputs**: DB intent; schema knowledge (231 tables); mapped business terminology; scope + timeframe constraints.
- **Internal processing**:
  - Build query plan (metrics, tables, joins, filters).
  - Generate SQL with guardrails (SELECT-only; LIMIT for lists; bounded date filters).
  - Execute; post-process (aggregates, breakdowns, anomaly detection); format in business language.
- **Validation logic**:
  - Enforce **read-only SQL**; block write operations.
  - **Dangerous keyword blocking** and query-shape constraints (joins/runtime/row limits).
  - Tenant/client scope enforcement; output redaction for sensitive fields (PII).
- **Output format**: Answer + key metrics + short “how computed” summary; optional SQL snippet for authorized roles.
- **Failure handling**: If unsafe/slow → request narrower timeframe, return aggregates only, or decline with guidance.
- **Edge cases**: Ambiguous definitions (“active deals”) require mapping disclosure; schema ambiguity requires conservative joins.

## 2.5 Jira Ticket Retrieval Workflow (Sprint + Assignee Filtering)

- **Objective**: Provide sprint status and ticket intelligence from Jira in natural language.
- **Inputs**: Jira key(s); sprint identifier; assignee name; Jira REST API v3 credentials; allowed projects.
- **Internal processing**:
  - Resolve assignee identity (name/email → accountId); resolve sprint naming/ids.
  - Build JQL/API requests; paginate; rate-limit handling.
  - Summarize issues (status, priority, ownership, blockers, updated timestamps).
- **Validation logic**: Permission enforcement (no restricted content leakage); project scoping; query limits.
- **Output format**: Ticket summary or sprint report with keys, counts, and follow-up suggestions.
- **Failure handling**: Permission denied → disclose access issue; sprint not found → suggest nearest match.
- **Edge cases**: Duplicate names; mixed-project sprints; incomplete metadata.

## 2.6 Confluence Semantic Search + RAG Retrieval

- **Objective**: Answer “how/why/what” questions grounded in Confluence documentation with citations.
- **Inputs**: Question; allowed spaces; indexed corpus (**793 documents**); embedding model + vector store.
- **Internal processing**:
  - Create embeddings; run **vector similarity matching**; retrieve top-k snippets.
  - Filter by access and recency; generate grounded answer; attach citations.
- **Validation logic**: Access enforcement; require retrieved evidence for factual claims; low-confidence → “not found” guidance.
- **Output format**: Explanation + citations (page titles/refs) + related docs (top 3).
- **Failure handling**: If retrieval confidence is low, propose keywords and where to look.
- **Edge cases**: Conflicting docs → prefer latest and call out discrepancies.

## 2.7 Business Terminology Mapping + Context-Aware Response Generation

- **Objective**: Ensure consistent business meaning (dealership workflows) and produce clear, stakeholder-ready answers.
- **Inputs**: Extracted terms (“desking”, “approved credit apps”, “active deals”); session memory; retrieved results.
- **Internal processing**:
  - Normalize terms → canonical definitions/filters; apply across DB/Jira/RAG.
  - Synthesize response: answer-first, consistent terminology, assumptions disclosed, citations included.
  - Persist/retain context (scope, entities) for follow-ups; allow reset on request.
- **Validation logic**: PII redaction; deny-by-default for bulk exports; prompt-injection resistance; no secret exfiltration.
- **Output format**: Summary → key results → evidence/citations → recommended next questions.
- **Failure handling**: Provide partial results + remediation; avoid hallucinations when sources are missing.
- **Edge cases**: User follow-up reuses memory (“break down by dealership”); scope changes mid-thread.

---

# 3. Process Flow (MAIN FOCUS)

## 3.1 End-to-End Architecture Flow

```text
+------------------+
|      User        |
|  Web Chat UI     |
+------------------+
         |
         v
+------------------+        +--------------------------+
| Python FastAPI   |        | Security + Permissions   |
| Agent API        +------->| (scope, PII, policy)     |
+--------+---------+        +------------+-------------+
         |                               |
         v                               v
+----------------------+        +-----------------------+
| NLU (intent+entities)|        | Context Memory        |
+----+-----------+-----+        +-----------+-----------+
     |           |                         |
     v           v                         v
+--------+  +---------+  +------------------------+
| DB API |  | Jira    |  | Confluence RAG         |
| (SQL)  |  | Agent   |  | (vector retrieval)     |
+---+----+  +----+----+  +-----------+------------+
    |            |                    |
    +------------+--------------------+
                 |
                 v
      +--------------------------+
      | Response Synthesis       |
      | + Citations + Formatting |
      +--------------------------+
                 |
                 v
           +-----------+
           |   Answer  |
           +-----------+
```

## 3.2 User Request Lifecycle

```text
Prompt
  |
  v
Request Intake (normalize, capture session)
  |
  v
NLU (intent + entities + terminology mapping)
  |
  v
Intent Routing Plan (DB / Jira / RAG / multi-source)
  |
  v
Security Validation (scope + read-only + policy)
  |
  v
Execute Connectors (parallel/sequential)
  |
  v
Merge Results + Validate + Cite
  |
  v
Answer-first Response + Follow-ups
  |
  v
Update Context Memory (session)
```

## 3.3 NLP Processing Pipeline

```text
Text
 |
 v
Entity Extraction (AZ-####, sprint, assignee, business terms)
 |
 v
Intent Classification
 |         |          |
 v         v          v
DB Query   Jira Flow  Confluence RAG
 |         |          |
 v         v          v
Safe SQL   JQL/API     Vector Search (FAISS)
```

## 3.4 Intent Routing Flow

```text
Plan (intents + confidence)
  |
  +--> High confidence  -> execute
  |
  +--> Medium confidence-> execute with safe defaults + disclose assumptions
  |
  +--> Low confidence   -> ask clarification (single targeted question)
```

## 3.5 Database Query Execution Flow

```text
Business Question
  |
  v
Terminology Mapping -> Filters
  |
  v
SQL Plan (tables/joins/metrics)
  |
  v
SQL Safety Gate
  |-- enforce SELECT-only
  |-- block dangerous keywords/patterns
  |-- enforce scope + LIMIT
  v
Execute -> Aggregate -> Redact -> Summarize
```

## 3.6 Jira Integration Workflow

```text
Prompt ("Ashutosh tickets in sprint 16")
  |
  v
Resolve Identity + Sprint
  |
  v
Build JQL / REST v3 Requests
  |
  v
Fetch Issues (paging, rate limits)
  |
  v
Summarize (status/priority/blockers) + cite keys
```

## 3.7 Confluence RAG Retrieval Flow

```text
Question
  |
  v
Embed Query (Sentence Transformers)
  |
  v
Vector Similarity (FAISS)
  |
  v
Top-k Snippets (access + recency filters)
  |
  v
Grounded Answer + Citations (page titles)
```

## 3.8 Security Validation Flow

```text
Planned Action
  |
  v
Check Connector Permissions (DB/Jira/Confluence)
  |
  v
Enforce Scope (tenant/client/dealership)
  |
  v
Apply Safety Rules
  |-- read-only SQL
  |-- dangerous keyword blocking
  |-- output redaction (PII)
  v
Allow -> Execute
Deny  -> Safe refusal + remediation
```

## 3.9 Response Generation Pipeline

```text
Connector Results (DB/Jira/RAG)
   |
   v
Merge + Deduplicate + Resolve Conflicts
   |
   v
Format (answer-first + citations + assumptions)
   |
   v
Return Response + Suggested Follow-ups
```

## 3.10 Error Handling Workflow

```text
Connector Call
  |
  +--> Success -> continue
  |
  +--> Timeout/Rate limit -> retry/backoff or degrade gracefully
  |
  +--> Permission denied -> safe refusal + remediation steps
  |
  +--> Low confidence -> ask clarification / “not found” guidance
```

## 3.11 Context Memory Flow

```text
Turn N Response
  |
  v
Store (scope, ticket keys, sprint, key entities)
  |
  v
Turn N+1 uses memory for follow-ups
  |
  +--> User requests reset -> clear memory for session
```

---

# 4. Technical Specifications

The solution uses **OpenAI GPT-4o-mini** as the primary LLM within a **Python FastAPI-based Agent API** architecture, integrating a **MySQL** database (231 tables, **309 relationships**) with **read-only SQL execution enforcement** and **dangerous keyword blocking** for query safety; semantic retrieval is implemented using a **FAISS** vector store and **Sentence Transformers** for embedding generation, powering a **Retrieval-Augmented Generation (RAG)** pipeline over **793 indexed Confluence documents**, alongside **Jira REST API v3** and **Confluence REST API** integrations, with low-latency, context-aware orchestration and structured response formatting with citations.

---

# 5. Conclusion

Conversational AI Co-Pilot for A2Z improves operational efficiency by consolidating enterprise knowledge access into a single conversational experience, reducing manual searching and reliance on SQL specialists. With safe database querying, Jira sprint/ticket intelligence, and grounded Confluence RAG retrieval—wrapped in permission-aware governance and context retention—the platform is positioned to scale across additional domains and enable future enhancements such as richer business ontologies, improved governance controls, and deeper workflow automation.

# 1. Project Overview

## Executive Summary

**Conversational AI Co-Pilot for A2Z** was created to reduce the time employees spend searching for answers across disconnected enterprise systems. Today, teams must switch between **Jira**, **Confluence**, and **database tooling** (each with separate logins and query patterns). As a result, simple business questions often take **5–10 minutes**, and non-technical users frequently depend on engineers/analysts for SQL and data retrieval.

This project delivers a **single conversational interface** that provides natural-language access to:

- **MySQL** business data (natural language querying across **231 tables**)
- **Jira** (ticket intelligence, sprint tracking)
- **Confluence** (RAG-based retrieval over **793 indexed documents**)
- **Dealership/business terminology** (e.g., “desking”, “approved credit apps”, “active deals”)

Example queries:

- “How many leads are in desking?”
- “Show Ashutosh tickets in sprint 16”
- “Summarize Jira AZ-54628”
- “Explain DynamoDB optimization strategy”

Business impact:

- **~90% faster information retrieval**
- **Reduced dependency on SQL expertise**
- **Higher organizational knowledge accessibility** via consistent answers and citations

---

# 2. Functional Specifications (MOST IMPORTANT SECTION)

This section defines **exactly what the assistant must do** when handling requests across database, Jira, and Confluence—covering user flow, routing, validation, and edge cases.

## 2.1 End-to-End User Interaction Flow

### Inputs

- Natural language prompt (single/multi-turn)
- Optional context: user identity/role, tenant/client scope, prior conversation history

### Processing

- Normalize text, extract entities (ticket keys, sprints, people, domain terms)
- Classify intent(s) and build a routing plan (DB/Jira/Confluence or multi-source)
- Enforce security + scope checks before any retrieval/execution
- Execute retrieval (parallel when possible), synthesize response, and optionally persist history/audit metadata

### Outputs

- “Answer-first” response with:
  - Key result(s) and assumptions (if any)
  - Source attribution (Jira keys, Confluence page titles, DB query summary)
  - Follow-up question(s) when ambiguity is material

### Validation logic

- Size/timeouts/rate limits; deny-by-default for sensitive requests
- No raw bulk exports; limit rows; prefer aggregates and summaries
- No leaking stack traces or internal instructions

### Edge cases

- Ambiguous scope (“which client/dealership?”) → ask one targeted clarifier
- Multi-part prompts → split and return a single consolidated answer
- Partial source failures → provide best-effort answer + clear disclosure

---

## 2.2 Query Understanding, Intent Classification, and Terminology Mapping

### Inputs

- Prompt text + prior turns
- Domain lexicon (dealership terminology and synonyms)

### Processing

- **Entity extraction**:
  - Jira keys (e.g., `AZ-54628`)
  - Sprint identifiers (“sprint 16”)
  - Assignees (names → identity mapping)
  - Business terms (“desking”, “active deals”, “approved credit apps”)
- **Intent classification** (may be multi-intent):
  - DB analytics/query
  - Jira lookup/report/sprint tracking
  - Confluence knowledge retrieval/explanation (RAG)
  - Multi-source orchestration
- **Terminology mapping**:
  - Normalize business language → canonical concepts/filters (e.g., “active deals” → status set)
  - Apply mappings consistently in SQL generation and document retrieval keywords

### Outputs

- Intent(s) + confidence
- Extracted entities + normalized terms
- Execution plan (sources + order + constraints)

### Validation logic

- Require mandatory entities when applicable (e.g., Jira key for “summarize ticket”)
- If mapping confidence is low, ask a single clarification rather than guessing

### Edge cases

- “Explain DynamoDB optimization strategy” → treat as Confluence/RAG by default
- Same term differs across clients/teams → require explicit scope or disclose assumptions

---

## 2.3 Database Querying (Natural Language → Safe SQL)

### Inputs

- Business question
- Schema knowledge (231 tables, joins, key metrics)
- Scope constraints (client/dealership), time window, and terminology mapping

### Processing

- Build query plan: metric(s), tables, join path, filters (status/time/scope)
- Generate **read-only** SQL:
  - SELECT-only, row limits for listings, bounded filters for large datasets
- Execute and post-process:
  - Aggregate formatting, breakdowns, anomaly checks, business-language summary

### Outputs

- Answer with key metrics and a short “how computed” explanation
- Optional query summary/SQL snippet (policy-controlled)

### Validation logic

- Block non-SELECT statements; enforce tenant/client boundaries
- Complexity and performance caps (joins/runtime/row count)
- Redact sensitive fields (PII) and prevent bulk exports

### Edge cases

- Slow or wide query → request narrower timeframe or return partial aggregates
- Schema ambiguity → fall back to best-known relationships and disclose limitations

---

## 2.4 Jira Intelligence (Tickets and Sprint Tracking)

### Inputs

- Ticket key (e.g., `AZ-54628`), assignee (“Ashutosh”), sprint (“sprint 16”)
- Jira base URL + API credentials + allowed project keys

### Processing

- Resolve sprint and assignee identity (name/email → accountId)
- Fetch issues via API/JQL; handle pagination and rate limits
- Summarize:
  - Status, priority, assignee, last updated
  - Highlights (description/acceptance criteria where permitted)
  - Actionable insights (blockers, next steps)

### Outputs

- Ticket summary or sprint report (counts + key items)
- Links/keys and follow-up suggestions (e.g., “show blockers only”)

### Validation logic

- Permission enforcement: do not disclose restricted ticket content
- Respect project scoping and query limits

### Edge cases

- Name ambiguity → ask user to disambiguate
- Sprint not found → suggest closest match

---

## 2.5 Confluence Retrieval (RAG over 793 Documents)

### Inputs

- Natural language question
- Indexed Confluence corpus (793 documents), optional space filters

### Processing

- Embed query → vector search → retrieve top-k snippets
- Filter by access rules and recency; generate grounded answer
- Produce citations (page title + reference)

### Outputs

- Explanation with citations (what docs were used)
- “Not found” guidance when retrieval confidence is low

### Validation logic

- Enforce space/page access controls
- Prevent hallucination by requiring retrieval support for factual claims

### Edge cases

- Conflicting docs → prefer latest and call out discrepancies
- Too many matches → cluster and return top categories + top 3 docs

---

## 2.6 Multi-Source Orchestration, Security, and Response Quality

### Inputs

- Execution plan (DB/Jira/Confluence), user identity/role, session context

### Processing

- Orchestrate calls (parallel where independent; sequential when dependent)
- Enforce governance:
  - Connector-level authz, tenant/client boundaries, read-only DB constraints
  - Output filtering (PII redaction), result limiting, prompt-injection defenses
- Response synthesis:
  - Answer-first, evidence-backed, consistent terminology, clear assumptions
- Context retention:
  - Remember entities (ticket key, sprint, scope) across turns; allow user to reset

### Outputs

- Final response with citations and disclosed limitations
- Best-effort partial responses when safe; remediation steps on denial/failure

### Validation logic

- Deny-by-default for bulk export requests (e.g., “export all customers”)
- No secrets exfiltration (from docs or environment), no internal prompt leakage

### Edge cases

- Conflicts across sources → present both + recommended authority
- Partial outages → degrade gracefully and keep user productive

---

# 3. Process Flow 

## 3.1 High-Level Architecture Flow

```text
User (Web UI)
   |
   v
API (FastAPI) / Orchestrator
   |
   +--> Intent + Entity Extraction
           |
           +--> DB Query Agent (MySQL, 231 tables)
           +--> Jira Agent (tickets/sprints)
           +--> Confluence RAG Agent (793 docs)
           |
           v
     Security + Scope Validation
           |
           v
   Response Synthesis + Citations
           |
           v
        Answer to User
```

## 3.2 User Request Lifecycle

```text
Prompt
  |
  v
Normalize + Extract Entities
  |
  v
Classify Intent(s) + Build Plan
  |
  v
Authorize + Enforce Scope/Policies
  |
  v
Retrieve/Execute (DB/Jira/RAG)
  |
  v
Merge + Validate + Cite Sources
  |
  v
Final Response (answer-first) + Follow-ups
```

## 3.3 RAG + SQL + Jira Pipelines (Combined View)

```text
                 +------------------+
                 | Intent Routing   |
                 +---+----------+---+
                     |          |
           +---------+          +---------+
           |                              |
           v                              v
  +--------+--------+            +--------+--------+
  | Confluence RAG  |            | Jira Intelligence|
  | (793 docs)      |            | (issues/sprints) |
  +--------+--------+            +--------+--------+
           |                              |
           v                              v
   Citations + Summary             Tickets + Metrics
           \                              /
            \                            /
             v                          v
              +-----------+  +----------+
              | DB Agent  |  | Security |
              | (Safe SQL)|  | + Scope  |
              +-----+-----+  +----+-----+
                    |             |
                    v             v
                 DB Results   Redaction/Policy
                    \             /
                     v           v
                 +-------------------+
                 | Response Synthesis|
                 +-------------------+
```

