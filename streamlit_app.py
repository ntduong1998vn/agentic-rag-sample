"""
Streamlit Chatbot Interface for Agentic RAG System
A beautiful, modern chatbot interface with support for document upload and chat.
"""

import streamlit as st
import requests
import time
from typing import Optional, Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Agentic RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 80%;
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Headers */
    h1 {
        color: white;
        text-align: center;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    h2, h3 {
        color: white;
        font-weight: 600;
    }
    
    /* Input fields */
    .stTextInput input, .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.9);
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader */
    .uploadedFile {
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.9);
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stInfo {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "collection_name" not in st.session_state:
    st.session_state.collection_name = "default"
if "chatbot_id" not in st.session_state:
    st.session_state.chatbot_id = None


def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_file(file, collection_name: str) -> Dict[str, Any]:
    """Upload a file to the API"""
    try:
        files = {"file": (file.name, file, file.type)}
        data = {"collection_name": collection_name}
        response = requests.post(
            f"{API_BASE_URL}/files/upload",
            files=files,
            data=data,
            timeout=300
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_message(message: str, collection_name: str, chatbot_id: Optional[int] = None) -> Dict[str, Any]:
    """Send a chat message to the API"""
    try:
        payload = {
            "message": message,
            "collection_name": collection_name
        }
        if chatbot_id:
            payload["chatbot_id"] = chatbot_id
            
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_chatbots() -> list:
    """Get list of available chatbots"""
    try:
        response = requests.get(f"{API_BASE_URL}/chatbots", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return []


def get_collections() -> list:
    """Get list of available collections"""
    try:
        response = requests.get(f"{API_BASE_URL}/files/collections", timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return []


# Main Header
st.markdown("<h1>🤖 Agentic RAG Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: white; font-size: 1.2rem;'>Powered by Google Gemini & Qdrant Vector Database</p>", unsafe_allow_html=True)

# Check API health
api_status = check_api_health()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # API Status
    if api_status:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
        st.warning("Please ensure the FastAPI server is running at http://localhost:8000")
    
    st.markdown("---")
    
    # Collection selection
    st.markdown("#### 📚 Document Collection")
    collections = get_collections() if api_status else []
    
    if collections:
        collection_options = ["default"] + [c.get("name", c) for c in collections if isinstance(c, dict)]
        st.session_state.collection_name = st.selectbox(
            "Select Collection",
            options=collection_options,
            index=0
        )
    else:
        st.session_state.collection_name = st.text_input(
            "Collection Name",
            value=st.session_state.collection_name,
            help="Enter the name of the document collection to use"
        )
    
    st.markdown("---")
    
    # Chatbot selection
    st.markdown("#### 🎭 Chatbot Personality")
    chatbots = get_chatbots() if api_status else []
    
    if chatbots:
        chatbot_options = {"Default (No specific personality)": None}
        for bot in chatbots:
            if isinstance(bot, dict) and "id" in bot and "name" in bot:
                chatbot_options[f"{bot['name']} - {bot.get('description', 'No description')}"] = bot["id"]
        
        selected_chatbot = st.selectbox(
            "Select Chatbot",
            options=list(chatbot_options.keys())
        )
        st.session_state.chatbot_id = chatbot_options[selected_chatbot]
    else:
        st.info("No chatbots available. Using default personality.")
        st.session_state.chatbot_id = None
    
    st.markdown("---")
    
    # File upload
    st.markdown("#### 📄 Upload Documents")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt", "md", "xlsx", "csv", "png", "jpg", "jpeg"],
        help="Upload documents to add to your knowledge base"
    )
    
    if uploaded_file and st.button("📤 Upload", use_container_width=True):
        if not api_status:
            st.error("API is not connected!")
        else:
            with st.spinner("Uploading and processing..."):
                result = upload_file(uploaded_file, st.session_state.collection_name)
                if result["success"]:
                    st.success(f"✅ File uploaded successfully!")
                    st.json(result["data"])
                else:
                    st.error(f"❌ Upload failed: {result['error']}")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("#### ℹ️ About")
    st.markdown("""
    This chatbot uses:
    - **Google Gemini** for AI responses
    - **Qdrant** for vector search
    - **RAG** for accurate answers
    
    Upload documents and ask questions!
    """)

# Main chat area
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        st.markdown(f"<div class='user-message'>👤 <strong>You:</strong><br>{content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='assistant-message'>🤖 <strong>Assistant:</strong><br>{content}</div>", unsafe_allow_html=True)
        
        # Show sources if available
        if "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**Source {i}:**")
                    if isinstance(source, dict):
                        st.json(source)
                    else:
                        st.text(source)

st.markdown("</div>", unsafe_allow_html=True)

# Chat input (always at the bottom)
user_input = st.chat_input("💬 Type your message here..." if api_status else "⚠️ API not connected")

if user_input:
    if not api_status:
        st.error("Cannot send message: API is not connected!")
    else:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Send to API and get response
        with st.spinner("🤔 Thinking..."):
            result = send_message(
                user_input,
                st.session_state.collection_name,
                st.session_state.chatbot_id
            )
            
            if result["success"]:
                response_data = result["data"]
                assistant_message = {
                    "role": "assistant",
                    "content": response_data.get("response", "No response received"),
                }
                
                # Add sources if available
                if "sources" in response_data:
                    assistant_message["sources"] = response_data["sources"]
                
                st.session_state.messages.append(assistant_message)
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {result['error']}"
                })
        
        # Rerun to display new messages
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<p style='text-align: center; color: white; opacity: 0.8;'>
    Made with ❤️ using Streamlit, FastAPI & LangChain | 
    <a href='http://localhost:8000/docs' target='_blank' style='color: white;'>API Docs</a>
</p>
""", unsafe_allow_html=True)
