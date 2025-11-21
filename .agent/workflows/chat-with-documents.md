---
description: chat with ingested documents
---

# Chat with Documents

This workflow shows how to interact with the chat API to query ingested documents.

## Prerequisites

- Development server is running
- Documents have been ingested into collections
- Know your collection name

## Basic Chat Request

1. Send a chat request via curl:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is this document about?",
       "collection_name": "your_collection_name"
     }'
   ```

2. Or use the interactive API docs:
   - Go to http://localhost:8000/docs
   - Find POST `/chat`
   - Click "Try it out"
   - Enter your message and collection name
   - Execute

## Streaming Chat Request

3. For streaming responses (better UX):
   ```bash
   curl -X POST "http://localhost:8000/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Explain the main concepts",
       "collection_name": "your_collection_name"
     }'
   ```

## Request Parameters

- `message` (required): Your question or query
- `collection_name` (required): Collection to search in
- `chatbot_id` (optional): Use a specific chatbot configuration
- `top_k` (optional): Number of relevant chunks to retrieve (default: 5)
- `threshold` (optional): Minimum similarity score (default: 0.7)

## Advanced Chat with Chatbot

4. Create a chatbot with custom settings:
   ```bash
   curl -X POST "http://localhost:8000/chatbots" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Technical Support Bot",
       "description": "Answers technical questions",
       "system_prompt": "You are a helpful technical support assistant.",
       "model": "gemini-2.0-flash-exp",
       "temperature": 0.7,
       "max_tokens": 2048,
       "qdrant_collection": "technical_docs"
     }'
   ```

5. Use the chatbot in a chat request:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How do I configure this feature?",
       "chatbot_id": 1
     }'
   ```

## Response Format

The API returns:
- `response`: The AI-generated answer
- `sources`: List of relevant document chunks used
- `metadata`: Information about the retrieval and generation

## Tips

- Use specific questions for better results
- Longer context messages may require higher max_tokens
- Adjust temperature (0.0-1.0) for creativity vs. consistency
- Use streaming for responsive user experience
- Monitor token usage in production

## Troubleshooting

- If no relevant context found: check collection name and document content
- If responses are off-topic: adjust similarity threshold
- If responses are cut off: increase max_tokens
- Check logs for detailed error information
