import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

# Local imports
from app.services.rag_service import get_rag_service, RAGService
from app.dto.chat import ChatRequest, ChatResponse, SourceDocument
from app.config.logging_config import get_logger
from app.config.settings import settings

# Configure logging
logger = get_logger(__name__)


class ChatbotService:
    """
    Chatbot service that combines RAG retrieval with LLM generation for stateless QA
    """

    def __init__(self):
        """Initialize the chatbot service"""
        self.rag_service = get_rag_service()

        # Initialize Gemini LLM
        self.llm = self._initialize_llm()

        # Create prompt template for RAG
        self.rag_prompt = self._create_rag_prompt()

        logger.info("Initialized ChatbotService")

    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize Gemini 2.5 Flash-Lite model"""
        try:
            api_key = settings.google_api_key
            if not api_key:
                raise ValueError("GOOGLE_API_KEY is not set in settings")

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",  # Gemini 2.5 Flash-Lite equivalent
                google_api_key=api_key,
                temperature=0.1,
                max_tokens=2048,
                streaming=True
            )

            logger.info("Successfully initialized Gemini 2.5 Flash-Lite model")
            return llm

        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def _create_rag_prompt(self) -> ChatPromptTemplate:
        """Create RAG prompt template"""
        template = """You are a helpful AI assistant that answers questions based on the provided context.

CONTEXT:
{context}

USER QUESTION: {question}

Instructions:
1. Use the provided context to answer the user's question
2. If the context doesn't contain relevant information, say so clearly
3. Be conversational and natural in your responses
4. Reference the sources when appropriate
5. Answer in the same language as the user's question (Japanese or English)

Answer:"""

        return ChatPromptTemplate.from_template(template)

    async def chat(
        self,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Process a chat request and return response

        Args:
            request: Chat request with query

        Returns:
            ChatResponse with answer and sources
        """
        start_time = time.time()

        try:
            # Retrieve relevant documents using RAG
            logger.info(f"Retrieving documents for query: {request.query}")
            retrieval_result = await self.rag_service.query_documents(
                query=request.query,
                top_k=request.top_k or 5,
                similarity_threshold=request.similarity_threshold or 0.7
            )

            if not retrieval_result["success"]:
                logger.error(f"RAG retrieval failed: {retrieval_result.get('message', 'Unknown error')}")
                return ChatResponse(
                    success=False,
                    answer="Sorry, I encountered an error while searching for relevant information.",
                    query=request.query,
                    error_message=retrieval_result.get("message")
                )

            # Prepare context and sources
            context = self._prepare_context(retrieval_result["results"])
            sources = self._prepare_sources(retrieval_result["results"])

            # Generate response using LLM
            logger.info(f"Generating response with Gemini")
            answer = await self._generate_response(request.query, context)

            response_time = time.time() - start_time

            logger.info(f"Chat request processed successfully in {response_time:.2f}s")

            return ChatResponse(
                success=True,
                answer=answer,
                sources=sources,
                query=request.query,
                response_time=response_time
            )

        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}")
            return ChatResponse(
                success=False,
                answer="Sorry, I encountered an unexpected error while processing your request.",
                query=request.query,
                error_message=str(e)
            )

    async def chat_stream(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat request and stream response

        Args:
            request: Chat request with query

        Yields:
            JSON-formatted response chunks for streaming
        """
        start_time = time.time()

        try:
            # Send initial response
            yield self._format_stream_chunk({
                "type": "status",
                "status": "retrieving"
            })

            # Retrieve relevant documents
            logger.info(f"Retrieving documents for streaming query: {request.query}")
            retrieval_result = await self.rag_service.query_documents(
                query=request.query,
                top_k=request.top_k or 5,
                similarity_threshold=request.similarity_threshold or 0.7
            )

            if not retrieval_result["success"]:
                yield self._format_stream_chunk({
                    "type": "error",
                    "message": "Failed to retrieve relevant documents"
                })
                return

            # Send retrieval complete info
            sources = self._prepare_sources(retrieval_result["results"])
            yield self._format_stream_chunk({
                "type": "retrieval_complete",
                "sources_found": len(sources),
                "sources": [src.dict() for src in sources]
            })

            # Prepare context
            context = self._prepare_context(retrieval_result["results"])

            # Stream response generation
            logger.info(f"Starting streaming response generation")
            full_response = ""

            async for chunk in self._generate_response_stream(request.query, context):
                if chunk:
                    full_response += chunk
                    yield self._format_stream_chunk({
                        "type": "content",
                        "content": chunk
                    })

            # Send completion info
            response_time = time.time() - start_time
            yield self._format_stream_chunk({
                "type": "complete",
                "response_time": response_time
            })

        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            yield self._format_stream_chunk({
                "type": "error",
                "message": "An unexpected error occurred"
            })

    def _prepare_context(self, retrieval_results: List[Dict]) -> str:
        """Prepare context from retrieval results"""
        if not retrieval_results:
            return "No relevant documents found."

        context_parts = []
        for i, result in enumerate(retrieval_results, 1):
            text = result.get("text", "").strip()
            metadata = result.get("metadata", {})
            file_name = metadata.get("file_name", f"Document {i}")

            context_parts.append(f"[Source {i}: {file_name}]\n{text}")

        return "\n\n".join(context_parts)

    def _prepare_sources(self, retrieval_results: List[Dict]) -> List[SourceDocument]:
        """Prepare source document information"""
        sources = []
        for result in retrieval_results:
            metadata = result.get("metadata", {})

            source = SourceDocument(
                file_name=metadata.get("file_name", "Unknown"),
                file_path=metadata.get("file_path", ""),
                chunk_text=result.get("text", ""),
                similarity_score=result.get("score", 0.0),
                metadata=metadata
            )
            sources.append(source)

        return sources

    async def _generate_response(self, question: str, context: str) -> str:
        """Generate response using Gemini LLM"""
        try:
            # Format prompt with context
            prompt_value = self.rag_prompt.format(
                context=context,
                question=question
            )

            # Generate response
            response = await self.llm.ainvoke(prompt_value)
            return response.content

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while generating a response."

    async def _generate_response_stream(self, question: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response using Gemini LLM"""
        try:
            # Format prompt with context
            prompt_value = self.rag_prompt.format(
                context=context,
                question=question
            )

            # Generate streaming response
            async for chunk in self.llm.astream(prompt_value):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error in streaming response generation: {str(e)}")
            yield "I apologize, but I encountered an error while generating a response."

    def _format_stream_chunk(self, data: Dict) -> str:
        """Format data for streaming response"""
        import json
        return f"data: {json.dumps(data)}\n\n"


# Global chatbot service instance
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Get the global chatbot service instance"""
    global _chatbot_service

    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
        logger.info("Initialized global chatbot service")

    return _chatbot_service