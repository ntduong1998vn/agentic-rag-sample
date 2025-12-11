# RAG Tools

## Current Tools

### 1. `unified_search_tool.py` ⭐ **RECOMMENDED**
Unified search tool that combines the functionality of both general knowledge base search and document-specific search.

**Features:**
- General knowledge base search (when `document_name` is not provided)
- Document-specific search (when `document_name` is provided)
- Parent Document Retriever with adjacent chunk expansion
- Similarity score threshold filtering (default: 0.7)
- Automatic deduplication and sorting

**Usage:**
```python
from app.agents.tools.unified_search_tool import create_unified_search_tool

# Create tool
search_tool = create_unified_search_tool(
    collection_name="my_collection",
    chatbot_id=chatbot_id,
    conversation_id=conversation_id  # optional
)

# General search
result = search_tool.invoke({"query": "What is AI?"})

# Document-specific search
result = search_tool.invoke({
    "query": "pricing information",
    "document_name": "contract.pdf"
})
```

### 2. `document_check_tool.py`
Check if a specific document exists in the database.

**Usage:**
```python
from app.agents.tools.document_check_tool import create_document_check_tool

check_tool = create_document_check_tool(chatbot_id, conversation_id)
result = check_tool.invoke({"document_name": "contract.pdf"})
```

### 3. `document_summarize_tool.py`
Summarize the entire content of a specific document using map-reduce strategy.

**Usage:**
```python
from app.agents.tools.document_summarize_tool import create_document_summarize_tool

summarize_tool = create_document_summarize_tool(
    collection_name="my_collection",
    chatbot_id=chatbot_id,
    conversation_id=conversation_id
)
result = summarize_tool.invoke({"document_name": "report.pdf"})
```

## Deprecated Tools (Legacy)

### ⚠️ `rag_tool.py` - DEPRECATED
**Status:** Merged into `unified_search_tool.py`

This tool provided general knowledge base search functionality. It has been superseded by `unified_search_tool.py` which offers the same functionality plus document-specific search.

**Migration:**
```python
# OLD
from app.agents.tools.rag_tool import create_knowledge_base_tool
tool = create_knowledge_base_tool(collection_name)
result = tool.invoke({"query": "search query"})

# NEW
from app.agents.tools.unified_search_tool import create_unified_search_tool
tool = create_unified_search_tool(collection_name, chatbot_id, conversation_id)
result = tool.invoke({"query": "search query"})  # Same interface!
```

### ⚠️ `document_search_tool.py` - DEPRECATED
**Status:** Merged into `unified_search_tool.py`

This tool provided document-specific search functionality. It has been superseded by `unified_search_tool.py` which offers the same functionality through an optional `document_name` parameter.

**Migration:**
```python
# OLD
from app.agents.tools.document_search_tool import create_document_search_tool
tool = create_document_search_tool(collection_name, chatbot_id, conversation_id)
result = tool.invoke({"document_name": "file.pdf", "query": "search query"})

# NEW
from app.agents.tools.unified_search_tool import create_unified_search_tool
tool = create_unified_search_tool(collection_name, chatbot_id, conversation_id)
result = tool.invoke({"query": "search query", "document_name": "file.pdf"})
```

## Architecture

### Core Retrieval Logic
The `unified_search_tool.py` contains a reusable helper function `_retrieve_and_expand_chunks()` that:
1. Performs similarity search with score threshold
2. Applies Parent Document Retriever pattern (retrieves adjacent chunks)
3. Deduplicates results
4. Sorts by document_id and chunk_index

This helper is used internally by the unified tool for both general and document-specific searches.

### Tool Integration
All tools are integrated into the RAG agent via:
- `app/agents/workflows/rag_agent_legacy.py` - Legacy ReAct-style agent
- `app/agents/workflows/rag_agent/` - New LangGraph-based agent

## Migration Checklist

If you're updating code to use the unified tool:

- [x] Update imports from `rag_tool` to `unified_search_tool`
- [x] Update imports from `document_search_tool` to `unified_search_tool`
- [x] Update tool creation calls to use `create_unified_search_tool()`
- [x] Update agent prompts to reflect the unified tool interface
- [x] Update any documentation or comments referencing old tools
- [ ] (Optional) Remove deprecated `rag_tool.py` and `document_search_tool.py` files

## Benefits of Unified Tool

1. **Simplified Agent Configuration**: Only one tool to manage instead of two
2. **Consistent Interface**: Same retrieval logic and parameters for both use cases
3. **Better Maintainability**: Single source of truth for search logic
4. **Reduced Complexity**: Fewer tools for the LLM to choose from
5. **Flexible Usage**: Agent can decide whether to search generally or in a specific document
