# Conversational AI Agent API for A2Z

# 1. Project Summary

Dealership teams and platform teams previously depended on manual operational workflows to retrieve business information such as deal counts, active deals, lead pipeline metrics, desking workflow status, and approved credit application data. Most operational requests required dependency on technical or reporting teams to manually query enterprise databases and share updates through emails or internal communication channels.

To eliminate this dependency and improve operational efficiency, we developed a **Conversational AI Agent API Platform** that enables dealership and platform teams to retrieve enterprise operational data directly using natural language queries.

The solution acts as a centralized conversational intelligence layer capable of securely accessing enterprise databases, understanding dealership business terminology, generating optimized read-only SQL queries, and returning contextual business responses in real time.

The platform significantly reduced manual operational effort, accelerated business decision-making, and improved accessibility of enterprise data for non-technical users.

## Example Business Queries
- “How many deals were created today?”
- “Show active deals”
- “How many leads are currently in desking?”
- “How many approved credit applications exist?”
- “Show deal status breakdown”

## Business Impact
- Eliminated manual reporting dependency
- Reduced operational turnaround time by ~90%
- Faster access to dealership operational metrics
- Improved accessibility for non-technical users
- Centralized conversational access to enterprise data
- Scalable AI-driven operational intelligence platform

---

# 2. Functional Specifications

## A. Dealership Operations Intelligence

### Deal Creation Analytics
The Agent API retrieves real-time deal creation metrics based on dealership scope, operational filters, and time-based conditions.

#### Functional Behavior
- Understands natural language business questions
- Maps dealership terminology to enterprise schema definitions
- Generates optimized read-only SQL queries
- Returns aggregated operational metrics

#### Supported Capabilities
- Daily/weekly/monthly deal counts
- Deal creation trend analysis
- Status-wise deal breakdown
- Dealership-wise aggregation

---

### Lead Management Intelligence

The platform provides conversational access to dealership lead pipeline information.

#### Functional Behavior
- Retrieves lead counts and workflow stage distribution
- Supports timeframe-based operational filtering
- Generates summarized operational insights

#### Supported Capabilities
- Lead funnel tracking
- Lead stage analytics
- Source-based filtering
- Time-based lead analysis

---

### Desking Workflow Intelligence

The system understands dealership workflow terminology such as “desking” and maps it to operational workflow stages.

#### Functional Behavior
- Maps dealership terminology to workflow stages
- Retrieves associated workflow metrics
- Generates contextual workflow summaries

#### Supported Capabilities
- Desking-stage deal counts
- Workflow-stage tracking
- Stage-wise operational analysis

---

### Credit Application Intelligence

The Agent API provides conversational retrieval of dealership credit application information.

#### Functional Behavior
- Retrieves approval and application status metrics
- Computes operational approval trends
- Generates summarized business responses

#### Supported Capabilities
- Approved application counts
- Approval ratio calculations
- Lender/source-based filtering
- Time-based application analytics

---

### Deal Status Intelligence

The platform provides operational visibility into dealership deal statuses.

#### Functional Behavior
- Maps operational terms like “active deals”
- Retrieves status-wise deal breakdowns
- Generates summarized operational reporting

#### Supported Capabilities
- Active vs inactive deal tracking
- Deal lifecycle monitoring
- Deal status analytics
- Operational summaries

---

### Natural Language to SQL Execution

The core Agent API converts conversational business questions into optimized read-only SQL execution plans.

#### Functional Behavior
- Intent classification and entity extraction
- Schema-aware SQL generation
- Multi-table relationship handling
- Aggregation and summarization

#### Security Controls
- Read-only SQL enforcement
- Dangerous keyword blocking
- Query sanitization and validation
- Runtime and join-limit enforcement

---

# 3. ASCII Process Flow

## High-Level Architecture

```text
+------------------+
|      User        |
+------------------+
         |
         v
+----------------------+
| Conversational Agent |
| API (FastAPI)        |
+----------+-----------+
           |
           v
 +---------------------+
 | NLU + Intent Router |
 +----------+----------+
            |
            v
      +------------+
      | DB Agent   |
      | (SQL)      |
      +------+-----+
             |
             v
 +----------------------+
 | Response Synthesis   |
 | + Context Handling   |
 +----------------------+
             |
             v
      +-------------+
      | Final Answer|
      +-------------+
```

---

## User Request Lifecycle

```text
User Query
    ->
Intent Detection
    ->
Entity Extraction
    ->
Agent Routing
    ->
Security Validation
    ->
Database Retrieval
    ->
Aggregation & Analysis
    ->
Business Response
```

---

## Database Intelligence Flow

```text
Business Question
      ->
Terminology Mapping
      ->
SQL Generation
      ->
Security Validation
      ->
Read-only Execution
      ->
Aggregation
      ->
Business Summary Response
```

---

## Security Validation Flow

```text
Request
   ->
Scope Validation
   ->
Read-only SQL Enforcement
   ->
Query Sanitization
   ->
Response Validation
   ->
Secure Response Delivery
```

---

# 4. Technical Specifications

The Conversational AI Agent API platform was developed using a FastAPI-based architecture integrated with OpenAI GPT-4o-mini for conversational intelligence and response generation. The platform securely connects with enterprise MySQL systems containing 231 relational tables and operational mappings to support dealership operational use cases.

The architecture supports natural language processing, intelligent intent routing, read-only SQL execution, scalable API orchestration, and contextual response synthesis for enterprise conversational workflows.

## Technology Stack
- Python
- FastAPI
- OpenAI GPT-4o-mini
- MySQL
- REST-based Agent APIs

## Security Controls
- SQL sanitization and validation
- Read-only query enforcement
- Dangerous keyword blocking
- Output filtering and validation
- Enterprise access enforcement

---

# 5. Conclusion

The Conversational AI Agent API platform transformed how dealership teams and platform teams access enterprise operational data. By replacing manual reporting workflows with conversational enterprise intelligence, the solution enabled real-time access to dealership operations and business metrics through a unified AI-driven interface.

The platform reduced operational delays, improved accessibility of enterprise information, and established a scalable foundation for future AI-driven operational automation and intelligent business workflows.