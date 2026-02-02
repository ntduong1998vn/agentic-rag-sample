from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI

GEMINI_LLM_MODEL = "gemini-2.5-flash-preview-09-2025"

def get_llm():
    return ChatGoogleGenerativeAI(
        model=GEMINI_LLM_MODEL,
        temperature=0,
        api_key=settings.google_api_key,
        # thinking_level="medium",
        include_thoughts=True,
    )
