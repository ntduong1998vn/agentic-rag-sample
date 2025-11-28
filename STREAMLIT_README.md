# Streamlit Chatbot Interface

## 🚀 Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Start the FastAPI Backend
In one terminal:
```bash
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Streamlit App
In another terminal:
```bash
uv run streamlit run streamlit_app.py
```

The Streamlit app will be available at **http://localhost:8501**

## ✨ Features

### 🎨 Beautiful UI
- Modern gradient background with glassmorphism effects
- Smooth message bubbles with shadows
- Interactive hover effects
- Premium, state-of-the-art design

### 💬 Chat Interface
- Real-time chat with the Agentic RAG system
- Message history with user and assistant messages
- Source citations for answers
- Streaming-ready architecture

### 📁 File Upload
- Upload documents (PDF, DOCX, TXT, MD, XLSX, CSV, images)
- Automatic processing and ingestion into vector database
- Select target collection for document organization

### 🤖 Chatbot Selection
- Choose from available chatbot personalities
- Different system prompts and configurations
- Custom knowledge bases per chatbot

### 📚 Collection Management
- View and select from available document collections
- Create new collections on-the-fly
- Collection-specific search and retrieval

### 🔄 Real-time Status
- API connection status indicator
- Loading states for file uploads
- Thinking animation during responses

## 🎯 Usage

1. **Connect to API**: Ensure the FastAPI backend is running (green status indicator)
2. **Select Collection**: Choose or create a document collection in the sidebar
3. **Upload Documents**: Use the file uploader to add documents to your knowledge base
4. **Choose Personality**: Select a chatbot personality (optional)
5. **Start Chatting**: Type your questions in the chat input at the bottom

## 🛠️ Configuration

The app connects to the FastAPI backend at `http://localhost:8000` by default.

To change the API URL, edit the `API_BASE_URL` variable in `streamlit_app.py`:

```python
API_BASE_URL = "http://your-custom-url:port"
```

## 📸 Screenshots

The interface features:
- Gradient purple background
- Glassmorphism chat container
- Color-coded message bubbles (purple for user, pink-red for assistant)
- Clean, modern sidebar with all controls
- Responsive design

## 🎨 Design Philosophy

This chatbot interface follows modern web design principles:

1. **Visual Excellence**: Eye-catching gradients and smooth transitions
2. **User Experience**: Intuitive layout with clear visual hierarchy
3. **Functionality**: All features accessible without overwhelming the user
4. **Premium Feel**: Polished animations and high-quality styling

## 🔧 Troubleshooting

### API Not Connected
- Ensure FastAPI is running: `uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Check that port 8000 is not blocked by firewall
- Verify the API_BASE_URL in the code

### Streamlit Won't Start
- Make sure dependencies are installed: `uv sync`
- Check that port 8501 is available
- Try clearing Streamlit cache: `streamlit cache clear`

### Upload Fails
- Check file size (very large files may timeout)
- Ensure the file format is supported
- Verify the collection name is valid

## 📝 Notes

- The app maintains chat history in session state (cleared on page refresh)
- File uploads are processed synchronously (may take time for large files)
- Sources are displayed in expandable sections under assistant messages
- The app automatically detects available chatbots and collections from the API

## 🚀 Next Steps

Consider enhancing the app with:
- Chat history persistence (save to database)
- User authentication
- Multi-user support with separate chat sessions
- Voice input/output
- Image generation and display
- Advanced search filters
- Export chat history
- Custom themes and color schemes

---

Made with ❤️ using Streamlit, FastAPI, and LangChain
