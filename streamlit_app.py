"""
Streamlit Chatbot Interface for Agentic RAG System
A beautiful, modern chatbot interface with support for document upload and chat.
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"
API_V2_URL = f"{API_BASE_URL}/api/v2"

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
if "chatbot_id" not in st.session_state:
    st.session_state.chatbot_id = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "user_id" not in st.session_state:
    # Generate a random user_id for this session
    import uuid

    st.session_state.user_id = str(uuid.uuid4())
if "api_version" not in st.session_state:
    st.session_state.api_version = "v2"


def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


# ============================================================================
# Chatbot API Functions
# ============================================================================


def get_chatbots() -> List[Dict[str, Any]]:
    """Get list of available chatbots from /api/v1/chatbots/"""
    try:
        response = requests.get(f"{API_V1_URL}/chatbots/", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching chatbots: {e}")
        return []


def create_chatbot(
    name: str, model_name: str = "gemini-2.0-flash"
) -> Optional[Dict[str, Any]]:
    """Create a new chatbot"""
    try:
        payload = {"name": name, "model_name": model_name, "llm_config": {}}
        response = requests.post(f"{API_V1_URL}/chatbots/", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating chatbot: {e}")
        return None


# ============================================================================
# Conversation API Functions
# ============================================================================


def get_conversations(chatbot_id: str) -> List[Dict[str, Any]]:
    """Get list of conversations for a chatbot"""
    try:
        response = requests.get(
            f"{API_V1_URL}/chatbots/{chatbot_id}/conversations", timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching conversations: {e}")
        return []


def create_conversation(
    chatbot_id: str, user_id: str, title: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Create a new conversation for a chatbot"""
    try:
        payload = {"user_id": user_id, "title": title or "New Conversation"}
        response = requests.post(
            f"{API_V1_URL}/chatbots/{chatbot_id}/conversations",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating conversation: {e}")
        return None


def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """Get message history for a conversation"""
    try:
        response = requests.get(
            f"{API_V1_URL}/chatbots/conversations/{conversation_id}/messages", timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching messages: {e}")
        return []


# ============================================================================
# Chat API Functions
# ============================================================================


def send_message(
    conversation_id: str, message: str, api_version: str = "v2"
) -> Dict[str, Any]:
    """Send a chat message to the appropriate API version"""
    try:
        payload = {"message": message}

        # Choose API version
        if api_version == "v2":
            url = f"{API_V2_URL}/chatbots/conversations/{conversation_id}/chat"
        else:
            url = f"{API_V1_URL}/chatbots/conversations/{conversation_id}/chat"

        response = requests.post(
            url,
            json=payload,
            timeout=120,  # Longer timeout for agent processing
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return {"success": False, "error": error_detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# Document Upload API Functions
# ============================================================================


def upload_file_to_chatbot(chatbot_id: str, file) -> Dict[str, Any]:
    """Upload a file to a chatbot's knowledge base"""
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(
            f"{API_V1_URL}/chatbots/{chatbot_id}/ingest", files=files, timeout=300
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Main Header
st.markdown("<h1>🤖 Agentic RAG Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: white; font-size: 1.2rem;'>Powered by AWS Bedrock & OpenSearch Vector Database</p>", unsafe_allow_html=True)

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
    
    # API Version Selection
    st.markdown("#### � API Version")
    api_version = st.radio(
        "Select API Version",
        options=["v2", "v1"],
        index=0 if st.session_state.api_version == "v2" else 1,
        help="v2: Router Agent (Supervisor), v1: RAG Agent only",
        horizontal=True
    )
    st.session_state.api_version = api_version
    
    if api_version == "v2":
        st.caption("🚀 V2: Uses Router Agent to dispatch between RAG and GitLab agents")
    else:
        st.caption("📚 V1: Uses RAG Agent for document-based questions")
    
    st.markdown("---")
    
    # Chatbot selection
    st.markdown("#### 🤖 Select Chatbot")
    chatbots = get_chatbots() if api_status else []
    
    if chatbots:
        chatbot_options = {}
        for bot in chatbots:
            if isinstance(bot, dict) and "id" in bot and "name" in bot:
                label = f"{bot['name']} ({bot.get('model_name', 'unknown')})"
                chatbot_options[label] = bot["id"]
        
        if chatbot_options:
            selected_chatbot_label = st.selectbox(
                "Available Chatbots",
                options=list(chatbot_options.keys()),
                help="Select a chatbot to start a conversation"
            )
            selected_chatbot_id = chatbot_options[selected_chatbot_label]
            
            # Update session state if chatbot changed
            if st.session_state.chatbot_id != selected_chatbot_id:
                st.session_state.chatbot_id = selected_chatbot_id
                st.session_state.conversation_id = None
                st.session_state.messages = []
        else:
            st.warning("No valid chatbots found")
    else:
        st.info("No chatbots available")
        
        # Create new chatbot form
        with st.expander("➕ Create New Chatbot"):
            new_chatbot_name = st.text_input("Chatbot Name", placeholder="My Chatbot")
            new_chatbot_model = st.selectbox(
                "Model",
                options=["gemini-2.0-flash", "gemini-1.5-pro", "gpt-4", "claude-3-sonnet"]
            )
            if st.button("Create Chatbot", use_container_width=True):
                if new_chatbot_name:
                    result = create_chatbot(new_chatbot_name, new_chatbot_model)
                    if result:
                        st.success(f"✅ Created chatbot: {new_chatbot_name}")
                        st.rerun()
                else:
                    st.error("Please enter a chatbot name")
    
    st.markdown("---")
    
    # Conversation selection (only if chatbot is selected)
    if st.session_state.chatbot_id:
        st.markdown("#### 💬 Conversations")
        conversations = get_conversations(st.session_state.chatbot_id) if api_status else []
        
        # Create new conversation button
        if st.button("➕ New Conversation", use_container_width=True):
            new_conv = create_conversation(
                chatbot_id=st.session_state.chatbot_id,
                user_id=st.session_state.user_id,
                title=f"Chat {len(conversations) + 1}"
            )
            if new_conv:
                st.session_state.conversation_id = new_conv["id"]
                st.session_state.messages = []
                st.success("✅ Created new conversation")
                st.rerun()
        
        if conversations:
            conv_options = {}
            for conv in conversations:
                if isinstance(conv, dict) and "id" in conv:
                    label = conv.get("title", f"Conversation {conv['id'][:8]}...")
                    conv_options[label] = conv["id"]
            
            if conv_options:
                # Find current selection index
                current_labels = list(conv_options.keys())
                current_index = 0
                if st.session_state.conversation_id:
                    for i, (label, cid) in enumerate(conv_options.items()):
                        if cid == st.session_state.conversation_id:
                            current_index = i
                            break
                
                selected_conv_label = st.selectbox(
                    "Select Conversation",
                    options=current_labels,
                    index=current_index
                )
                selected_conv_id = conv_options[selected_conv_label]
                
                # Update session state if conversation changed
                if st.session_state.conversation_id != selected_conv_id:
                    st.session_state.conversation_id = selected_conv_id
                    st.session_state.messages = []
                    # Load messages from history
                    messages = get_conversation_messages(selected_conv_id)
                    for msg in messages:
                        role = "user" if msg.get("role") == "human" else "assistant"
                        content = msg.get("message", {}).get("content", "")
                        if content:
                            st.session_state.messages.append({
                                "role": role,
                                "content": content
                            })
        else:
            st.info("No conversations yet. Create one to start chatting!")
    
    st.markdown("---")
    
    # File upload (only if chatbot is selected)
    if st.session_state.chatbot_id:
        st.markdown("#### 📄 Upload Documents")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt", "md", "xlsx", "xls", "csv", "png", "jpg", "jpeg"],
            help="Upload documents to add to chatbot's knowledge base"
        )
        
        if uploaded_file and st.button("📤 Upload to Chatbot", use_container_width=True):
            if not api_status:
                st.error("API is not connected!")
            else:
                with st.spinner("Uploading and processing..."):
                    result = upload_file_to_chatbot(st.session_state.chatbot_id, uploaded_file)
                    if result["success"]:
                        st.success("✅ File uploaded successfully!")
                        if "data" in result:
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
    - **AWS Bedrock** for AI responses
    - **OpenSearch** for vector search
    - **RAG** for accurate answers
    - **Router Agent** for intelligent routing
    
    Select a chatbot and start chatting!
    """)

# Main chat area
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Show current session info
if st.session_state.chatbot_id and st.session_state.conversation_id:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"🤖 Chatbot: {st.session_state.chatbot_id[:8]}...")
    with col2:
        st.caption(f"💬 Conversation: {st.session_state.conversation_id[:8]}...")
    with col3:
        st.caption(f"🔄 API: {st.session_state.api_version.upper()}")

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
                        # Show metadata
                        metadata = source.get("metadata", source)
                        st.json(metadata)
                    else:
                        st.text(source)

st.markdown("</div>", unsafe_allow_html=True)

# Chat input - check for required session state
can_chat = api_status and st.session_state.chatbot_id and st.session_state.conversation_id

if not st.session_state.chatbot_id:
    placeholder_text = "⚠️ Please select a chatbot first"
elif not st.session_state.conversation_id:
    placeholder_text = "⚠️ Please create or select a conversation first"
elif not api_status:
    placeholder_text = "⚠️ API not connected"
else:
    placeholder_text = "💬 Type your message here..."

user_input = st.chat_input(placeholder_text)

if user_input:
    if not can_chat:
        if not st.session_state.chatbot_id:
            st.error("Please select a chatbot first!")
        elif not st.session_state.conversation_id:
            st.error("Please create or select a conversation first!")
        else:
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
                conversation_id=st.session_state.conversation_id,
                message=user_input,
                api_version=st.session_state.api_version
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
    Made with ❤️ using Streamlit, FastAPI & LangGraph | 
    <a href='http://localhost:8000/docs' target='_blank' style='color: white;'>API Docs</a>
</p>
""", unsafe_allow_html=True)

