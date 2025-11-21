---
description: manage chatbot configurations
---

# Manage Chatbots

This workflow covers CRUD operations for chatbot configurations.

## Prerequisites

- Development server is running
- PostgreSQL database is accessible

## Create a Chatbot

1. Create a new chatbot configuration:
   ```bash
   curl -X POST "http://localhost:8000/chatbots" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Customer Support Bot",
       "description": "Handles customer inquiries",
       "system_prompt": "You are a friendly customer support assistant. Always be helpful and polite.",
       "model": "gemini-2.0-flash-exp",
       "temperature": 0.7,
       "max_tokens": 2048,
       "qdrant_collection": "customer_docs",
       "top_k": 5,
       "threshold": 0.7
     }'
   ```

2. Response will include the created chatbot with its ID

## List All Chatbots

// turbo
3. Get all chatbots:
   ```bash
   curl -X GET "http://localhost:8000/chatbots"
   ```

4. With pagination:
   ```bash
   curl -X GET "http://localhost:8000/chatbots?skip=0&limit=10"
   ```

## Get a Specific Chatbot

// turbo
5. Get chatbot by ID:
   ```bash
   curl -X GET "http://localhost:8000/chatbots/1"
   ```

## Update a Chatbot

6. Update chatbot configuration:
   ```bash
   curl -X PUT "http://localhost:8000/chatbots/1" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Updated Bot Name",
       "description": "Updated description",
       "system_prompt": "Updated system prompt",
       "temperature": 0.8
     }'
   ```

## Delete a Chatbot

7. Delete a chatbot:
   ```bash
   curl -X DELETE "http://localhost:8000/chatbots/1"
   ```

## Chatbot Configuration Options

### Model Options
- `gemini-2.0-flash-exp` - Fast, general-purpose (recommended)
- `gemini-1.5-pro` - More capable, slower
- `gemini-1.5-flash` - Balanced performance

### Parameters
- `temperature` (0.0-1.0): Controls randomness
  - 0.0: Deterministic, consistent
  - 1.0: Creative, varied
  
- `max_tokens`: Maximum response length
  - 512: Short answers
  - 2048: Medium responses (default)
  - 4096: Long, detailed responses

- `top_k`: Number of document chunks to retrieve
  - 3-5: Focused context
  - 10+: Broader context

- `threshold`: Minimum similarity score (0.0-1.0)
  - 0.5: Lenient matching
  - 0.7: Standard (recommended)
  - 0.9: Strict matching

## Use Cases

### Technical Documentation Bot
```json
{
  "name": "Tech Docs Assistant",
  "system_prompt": "You are a technical documentation expert. Provide accurate, detailed answers with code examples when relevant.",
  "temperature": 0.3,
  "top_k": 10,
  "threshold": 0.75
}
```

### Creative Writing Assistant
```json
{
  "name": "Writing Helper",
  "system_prompt": "You are a creative writing assistant. Help users with storytelling, character development, and plot ideas.",
  "temperature": 0.9,
  "max_tokens": 4096
}
```

### Customer Support Bot
```json
{
  "name": "Support Assistant",
  "system_prompt": "You are a helpful customer support agent. Be empathetic, clear, and solution-focused.",
  "temperature": 0.5,
  "top_k": 5,
  "threshold": 0.7
}
```

## Tips

- Test different system prompts to find what works best
- Lower temperature for factual, consistent responses
- Higher temperature for creative, varied responses
- Adjust top_k based on document size and complexity
- Monitor chatbot performance and iterate on configurations
