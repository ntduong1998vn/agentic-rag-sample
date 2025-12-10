# Document QA Agent - System Design Diagrams & Flows

## 1. OVERALL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ Web UI   │   │ REST API │   │   CLI    │   │ Python   │            │
│  │ (React)  │   │(FastAPI) │   │ (Click)  │   │ Direct   │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │              │                   │
└───────┼──────────────┼──────────────┼──────────────┼───────────────────┘
        │              │              │              │
        └──────────────┼──────────────┼──────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER (FastAPI)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   /query     │  │  /upload     │  │ /documents   │                 │
│  │   /search    │  │  /status     │  │  /batch      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION LAYER (LangGraph)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    STATE GRAPH EXECUTION                        │   │
│  │                                                                 │   │
│  │  START ──→ [1.ANALYZE] ──→ [2.RETRIEVE] ──→ [3.GENERATE]      │   │
│  │                                                │                │   │
│  │                                                ▼                │   │
│  │                                         [4.EVALUATE] ──→ LOOP?  │   │
│  │                                                │                │   │
│  │                                     ┌──────────┴──────────┐    │   │
│  │                                     │                     │    │   │
│  │                                  YES │ Needs              │    │   │
│  │                                     │ Refinement         │    │   │
│  │                                     │                     │    │   │
│  │                                     ▼                     │    │   │
│  │                              [5.REFINE] ──────┘           │    │   │
│  │                                                 NO         │    │   │
│  │                                     ├──────────────────→ END    │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
        │                      │                      │
        │                      │                      │
        ▼                      ▼                      ▼
   ┌─────────┐            ┌──────────┐           ┌──────────┐
   │  TOOLS  │            │   LLM    │           │ VECTOR   │
   │ Module  │            │ (GPT-4o) │           │   DB     │
   └─────────┘            └──────────┘           │ (Chroma) │
                                                  └──────────┘
```

## 2. DETAILED AGENT NODES WORKFLOW

### Node 1: ANALYZE
```
INPUT: User Query
       │
       ▼
┌─────────────────────────────┐
│ Parse Query Intent          │
├─────────────────────────────┤
│ • Extract key terms         │
│ • Identify entity types     │
│ • Detect complexity level   │
│ • Classify query type       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Strategic Planning          │
├─────────────────────────────┤
│ • Determine retrieval needs │
│ • Select search strategy    │
│ • Plan refinement approach  │
└──────────┬──────────────────┘
           │
           ▼
OUTPUT: Query Analysis + Strategy
```

### Node 2: RETRIEVE
```
INPUT: Query + Strategy
       │
       ▼
┌─────────────────────────────┐
│ Vector Similarity Search    │
├─────────────────────────────┤
│ • Embed query               │
│ • Search vector store       │
│ • Return top-k results      │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Filter & Rank Results       │
├─────────────────────────────┤
│ • Apply similarity threshold│
│ • Rank by relevance        │
│ • Extract metadata         │
└──────────┬──────────────────┘
           │
           ▼
OUTPUT: Ranked Documents + Sources
```

### Node 3: GENERATE
```
INPUT: Query + Context Documents
       │
       ▼
┌─────────────────────────────┐
│ Build LLM Prompt            │
├─────────────────────────────┤
│ • Format context            │
│ • Add instructions          │
│ • Set output format         │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ LLM Inference               │
├─────────────────────────────┤
│ • Generate answer           │
│ • Include citations         │
│ • Assess confidence         │
└──────────┬──────────────────┘
           │
           ▼
OUTPUT: Answer + Confidence Score + Sources
```

### Node 4: EVALUATE
```
INPUT: Generated Answer
       │
       ▼
┌─────────────────────────────────┐
│ Quality Assessment Rubric        │
├─────────────────────────────────┤
│ ┌─────────────────────────────┐ │
│ │ Completeness (0-1)          │ │
│ │ Does it fully address query? │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Accuracy (0-1)              │ │
│ │ Is information correct?      │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ Clarity (0-1)               │ │
│ │ Is it well articulated?      │ │
│ └─────────────────────────────┘ │
└──────────┬──────────────────────┘
           │
           ▼
        Avg Score = 
        (Completeness + Accuracy + Clarity) / 3
           │
           ▼
┌─────────────────────────────────┐
│ Decision Logic                   │
├─────────────────────────────────┤
│ IF Score < 0.75 AND              │
│    Iterations < MAX              │
│ THEN Refine Needed ✓             │
│ ELSE Complete ✓                  │
└──────────┬──────────────────────┘
           │
OUTPUT: Decision (Continue or Complete)
```

### Node 5: REFINE
```
INPUT: Feedback + Original Answer
       │
       ▼
┌─────────────────────────────┐
│ Analyze Deficiencies        │
├─────────────────────────────┤
│ • Missing information?      │
│ • Unclear sections?         │
│ • Contradictions?           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Generate Improved Answer    │
├─────────────────────────────┤
│ • Add missing context       │
│ • Clarify unclear parts     │
│ • Resolve contradictions    │
└──────────┬──────────────────┘
           │
           ▼
OUTPUT: Improved Answer → Back to EVALUATE
```

## 3. DATA FLOW DIAGRAM

```
User Input Query
       │
       ▼
┌──────────────────────────────┐
│   QUERY VALIDATION           │
│   • Length check             │
│   • Sanitization             │
│   • Format check             │
└──────────┬───────────────────┘
           │
           ▼
   ┌───────────────────┐
   │ Initialize State  │
   │                   │
   │ query: str        │
   │ retrieved_docs: []│
   │ answer: ""        │
   │ sources: []       │
   │ iterations: 0     │
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────────────────────────────┐
   │ AGENT GRAPH EXECUTION                     │
   │ (State flows through all nodes)           │
   │                                           │
   │ graph.invoke(state)                       │
   │   → Returns: updated state with answer    │
   └─────────┬─────────────────────────────────┘
             │
             ▼
   ┌───────────────────┐
   │ RESULT FORMATTING │
   │                   │
   │ • Extract answer  │
   │ • Collect sources │
   │ • Get scores      │
   │ • Add metadata    │
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────┐
   │ RETURN TO USER    │
   │                   │
   │ {                 │
   │   status: success │
   │   answer: ...     │
   │   sources: [...]  │
   │   confidence: 0.95│
   │ }                 │
   └───────────────────┘
```

## 4. VECTOR DATABASE FLOW

```
DOCUMENT INGESTION PIPELINE
─────────────────────────────

Raw Documents (PDF, DOCX, XLSX)
       │
       ▼
┌──────────────────────────┐
│   Load Documents         │
│   (PyPDFLoader,          │
│    Docx2txtLoader, etc)  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Extract Text           │
│   + Metadata             │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Split into Chunks      │
│   (1000 tokens)          │
│   (200 overlap)          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Generate Embeddings    │
│   (text-embedding-3)     │
│   (1536 dimensions)      │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Store in Chroma        │
│   • Embeddings           │
│   • Text content         │
│   • Metadata             │
└────────┬─────────────────┘
         │
         ▼
   Persisted Vector DB


QUERY RETRIEVAL PIPELINE
─────────────────────────

User Query
       │
       ▼
┌──────────────────────────┐
│   Embed Query            │
│   (same model)           │
│   (1536 dimensions)      │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Cosine Similarity      │
│   Search (HNSW index)    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Rank by Score          │
│   Score = Similarity     │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Filter Results         │
│   threshold >= 0.3       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Return Top-K           │
│   (K = 5 by default)     │
└────────┬─────────────────┘
         │
         ▼
   Retrieved Context
```

## 5. STATE MACHINE DIAGRAM

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │    ANALYZE    │
              │               │
              │ Parse Query   │
              │ Plan Strategy │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   RETRIEVE    │
              │               │
              │ Vector Search │
              │ Get Top-K     │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   GENERATE    │
              │               │
              │ LLM Answer    │
              │ Add Citations │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │  EVALUATE     │
              │               │
              │ Score Output  │
              │ Decide Next   │
              └───┬───────┬───┘
                  │       │
        Good      │       │  Needs
        (Score    │       │  Refinement
         >0.75)   │       │  (Score <0.75)
                  │       │  (Iter <Max)
                  │       │
                  ▼       ▼
                 END    REFINE
                        │
                        ▼
                   Improve
                   Answer
                        │
                        └──→ (back to EVALUATE)
```

## 6. API ENDPOINT FLOW

```
CLIENT REQUEST
      │
      ├─→ POST /query
      │   │
      │   ├─→ Validate Input
      │   │
      │   ├─→ Call Agent.answer_question()
      │   │
      │   ├─→ Run State Graph
      │   │
      │   └─→ Return QueryResponse
      │
      ├─→ POST /upload
      │   │
      │   ├─→ Validate Files
      │   │
      │   ├─→ Save to Disk
      │   │
      │   └─→ Return File Info
      │
      ├─→ POST /reinitialize
      │   │
      │   ├─→ Run in Background
      │   │
      │   ├─→ Reload Documents
      │   │
      │   └─→ Rebuild Vector DB
      │
      ├─→ GET /search?query=...
      │   │
      │   ├─→ Call vector_db.retrieve()
      │   │
      │   └─→ Return Raw Results
      │
      ├─→ GET /documents
      │   │
      │   ├─→ List All Files
      │   │
      │   └─→ Return Document Info
      │
      └─→ POST /batch-query
          │
          ├─→ Loop through Queries
          │
          ├─→ Parallel/Sequential
          │
          └─→ Return Batch Results
```

## 7. CONFIGURATION HIERARCHY

```
DEFAULT CONFIG (hardcoded)
        ↓
    .env.template
        ↓
    .env (user created)
        ↓
    Environment Variables
        ↓
    Runtime Arguments
        ↓
    FINAL CONFIGURATION
```

## 8. PERFORMANCE METRICS CHAIN

```
Query Input
    │
    ├─→ Parse Time: ~50ms
    │
    ├─→ Embed Query: ~200ms
    │
    ├─→ Vector Search: ~300ms
    │
    ├─→ LLM Generation: ~3000-5000ms
    │
    ├─→ Evaluation: ~500-1000ms
    │
    └─→ Optional Refinement: +3000-5000ms
    
TOTAL: 3-8 seconds (typical)
       UP TO: 10+ seconds (with refinement)
```

## 9. ERROR HANDLING FLOW

```
Exception Occurs
       │
       ▼
   ┌───────────────────────────┐
   │ Catch Exception           │
   │ (try-except blocks)       │
   └────────┬──────────────────┘
            │
            ▼
   ┌───────────────────────────┐
   │ Log Error                 │
   │ (to logs/api.log)         │
   └────────┬──────────────────┘
            │
            ▼
   ┌───────────────────────────┐
   │ Determine Severity        │
   ├───────────────────────────┤
   │ • Connection Error        │
   │ • Input Validation Error  │
   │ • LLM Error               │
   │ • Database Error          │
   └────────┬──────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
  Retry       Return Error
  (if safe)    Response
    │          (4xx or 5xx)
    │
    └──────────→ User Response
```

## 10. DEPLOYMENT ARCHITECTURE

```
┌────────────────────────────────────────────────────┐
│                   PRODUCTION                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Load     │  │ Web      │  │ Database │       │
│  │ Balancer │→→│ Servers  │→→│ (Remote) │       │
│  │(NGINX)   │  │ (API)    │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                      ↑                            │
│                      │                            │
│              ┌───────┴────────┐                   │
│              │                │                   │
│         Vector DB        Redis Cache              │
│         (Managed)        (Session)                │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ Monitoring & Logging                      │   │
│  │ • CloudWatch / DataDog                    │   │
│  │ • Query performance metrics               │   │
│  │ • Error tracking                          │   │
│  │ • Cost monitoring                         │   │
│  └──────────────────────────────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

This comprehensive visual reference should help you understand every aspect of the system architecture, data flows, and processing workflows.
