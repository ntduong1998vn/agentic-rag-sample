"""
Integration tests for code ingestion pipeline.

Tests the complete flow from GitLab repository to vector store,
including chunking and embedding generation.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import asyncio

# Import services
from app.connectors.gitlab_connector import GitLabConnector
from app.rag.code_ingestion import CodeIngestionService, get_code_ingestion_service
from app.rag.ast_splitter import ASTCodeSplitter
from app.services.gitlab_service import GitLabRAGService


class TestCodeIngestionIntegration:
    """Integration tests for code ingestion"""

    @pytest.fixture
    def mock_gitlab_data(self):
        """Mock GitLab repository data"""
        return {
            "repository_name": "test-repo",
            "files": [
                {
                    "path": "src/main.py",
                    "content": '''def greet(name):
    """Greet a user."""
    return f"Hello, {name}!"

class Calculator:
    def add(self, a, b):
        return a + b
''',
                    "metadata": {
                        "file_path": "src/main.py",
                        "file_name": "main.py",
                        "file_size": 150,
                        "blob_id": "abc123",
                    }
                },
                {
                    "path": "src/utils.js",
                    "content": '''function formatDate(date) {
    return date.toISOString();
}

class APIClient {
    async fetchData(endpoint) {
        const response = await fetch(endpoint);
        return response.json();
    }
}
''',
                    "metadata": {
                        "file_path": "src/utils.js",
                        "file_name": "utils.js",
                        "file_size": 200,
                        "blob_id": "def456",
                    }
                },
                {
                    "path": "src/types.ts",
                    "content": '''interface User {
    id: number;
    name: string;
}

function createUser(data: User): User {
    return { ...data };
}
''',
                    "metadata": {
                        "file_path": "src/types.ts",
                        "file_name": "types.ts",
                        "file_size": 180,
                        "blob_id": "ghi789",
                    }
                },
                {
                    "path": "src/Service.php",
                    "content": '''<?php
namespace App\Services;

class UserService {
    public function getUser($id) {
        return User::find($id);
    }

    private function validate($data) {
        return true;
    }
}
?>
''',
                    "metadata": {
                        "file_path": "src/Service.php",
                        "file_name": "Service.php",
                        "file_size": 220,
                        "blob_id": "jkl012",
                    }
                }
            ]
        }

    @pytest.fixture
    def mock_gitlab_connector(self, mock_gitlab_data):
        """Create mocked GitLab connector"""
        connector = MagicMock(spec=GitLabConnector)

        # Mock repository tree
        connector.fetch_repository_tree = MagicMock(
            return_value=[{"path": f["path"], "type": "blob"} for f in mock_gitlab_data["files"]]
        )

        # Mock fetch all code files
        connector.fetch_all_code_files = MagicMock(
            return_value=mock_gitlab_data["files"]
        )

        # Mock to_documents
        from llama_index.core import Document
        documents = [
            Document(text=f["content"], metadata=f["metadata"])
            for f in mock_gitlab_data["files"]
        ]
        connector.to_documents = MagicMock(return_value=documents)

        connector.get_project_info = MagicMock(
            return_value={
                "id": 123,
                "name": mock_gitlab_data["repository_name"],
                "description": "Test repository",
                "web_url": "https://gitlab.com/test/test-repo",
                "default_branch": "main",
                "visibility": "private",
            }
        )

        connector.test_connection = MagicMock(return_value=True)

        return connector

    @pytest.fixture
    def ingestion_service(self, mock_gitlab_connector):
        """Create code ingestion service with mocked GitLab"""
        from app.rag.ast_splitter import ASTCodeSplitter

        splitter = ASTCodeSplitter(min_tokens=10, max_tokens=2000)

        service = CodeIngestionService(
            gitlab_connector=mock_gitlab_connector,
            ast_splitter=splitter
        )

        return service

    @pytest.mark.asyncio
    async def test_full_ingestion_pipeline(self, ingestion_service, mock_gitlab_data):
        """Test complete ingestion pipeline"""
        result = await ingestion_service.ingest_repository(ref="main")

        assert result["success"] is True
        assert "processed_chunks" in result["stats"]
        assert result["stats"]["total_files"] == len(mock_gitlab_data["files"])

        # Should have many chunks (files, classes, functions, methods)
        assert result["stats"]["processed_chunks"] > len(mock_gitlab_data["files"])

    @pytest.mark.asyncio
    async def test_ingestion_creates_different_chunk_types(self, ingestion_service):
        """Test that ingestion creates different chunk types"""
        result = await ingestion_service.ingest_repository(ref="main")

        chunks = result.get("chunks", [])

        # Check for different chunk types
        chunk_types = set(chunk.metadata.get("chunk_type") for chunk in chunks)

        assert "function" in chunk_types or "method" in chunk_types
        assert "class" in chunk_types

    @pytest.mark.asyncio
    async def test_ingestion_preserves_metadata(self, ingestion_service):
        """Test that metadata is preserved through ingestion"""
        result = await ingestion_service.ingest_repository(ref="main")

        chunks = result.get("chunks", [])

        for chunk in chunks:
            assert "file_path" in chunk.metadata
            assert "repository_name" in chunk.metadata or "chunk_type" in chunk.metadata

    def test_chunking_multiple_languages(self, ingestion_service):
        """Test that AST splitter handles all 4 languages"""
        from app.rag.ast_splitter import ASTCodeSplitter

        splitter = ASTCodeSplitter()

        # Test Python
        py_chunks = splitter.split_file("def test(): pass", "test.py")
        assert len(py_chunks) > 0

        # Test JavaScript
        js_chunks = splitter.split_file("function test() {}", "test.js")
        assert len(js_chunks) > 0

        # Test TypeScript
        ts_chunks = splitter.split_file("function test(): void {}", "test.ts")
        assert len(ts_chunks) > 0

        # Test PHP
        php_chunks = splitter.split_file(r"<?php function test() {} ?>", "test.php")
        assert len(php_chunks) > 0

    @pytest.mark.asyncio
    async def test_ingestion_service_error_handling(self, ingestion_service):
        """Test error handling during ingestion"""
        # Simulate error in one file
        ingestion_service.gitlab_connector.fetch_all_code_files = MagicMock(
            side_effect=Exception("GitLab API error")
        )

        result = await ingestion_service.ingest_repository(ref="main")

        assert result["success"] is False
        assert "error" in result["message"].lower()

    @pytest.fixture
    def gitlab_rag_service(self, mock_gitlab_connector):
        """Create GitLab RAG service with mocked dependencies"""
        from app.services.gitlab_service import GitLabRAGService
        from app.rag.code_ingestion import CodeIngestionService
        from app.rag.ast_splitter import ASTCodeSplitter

        splitter = ASTCodeSplitter()
        ingestion_service = CodeIngestionService(
            gitlab_connector=mock_gitlab_connector,
            ast_splitter=splitter
        )

        service = GitLabRAGService(
            gitlab_connector=mock_gitlab_connector,
            code_ingestion_service=ingestion_service
        )

        return service

    @pytest.mark.asyncio
    async def test_gitlab_service_search(self, gitlab_rag_service):
        """Test code search in GitLab RAG service"""
        # Mock vector store search
        mock_result = MagicMock()
        mock_result.node = MagicMock()
        mock_result.node.text = "def greet(name): return f'Hello, {name}!'"
        mock_result.node.metadata = {
            "file_path": "src/main.py",
            "chunk_type": "function",
            "language": "python",
            "chunk_name": "greet",
        }
        mock_result.score = 0.85

        gitlab_rag_service.vector_store_service.search = AsyncMock(
            return_value=[mock_result]
        )

        result = await gitlab_rag_service.search_code(
            query="greeting function",
            top_k=5
        )

        assert result["success"] is True
        assert result["total_results"] > 0

    @pytest.mark.asyncio
    async def test_gitlab_service_search_with_filters(self, gitlab_rag_service):
        """Test code search with language filter"""
        mock_result = MagicMock()
        mock_result.node = MagicMock()
        mock_result.node.text = "function test() {}"
        mock_result.node.metadata = {
            "file_path": "test.js",
            "chunk_type": "function",
            "language": "javascript",
        }
        mock_result.score = 0.90

        gitlab_rag_service.vector_store_service.search = AsyncMock(
            return_value=[mock_result]
        )

        result = await gitlab_rag_service.search_code(
            query="test function",
            language="javascript"
        )

        assert result["success"] is True
        assert all(r["language"] == "javascript" for r in result["results"])

    @pytest.mark.asyncio
    async def test_gitlab_service_full_repository_ingestion(self, gitlab_rag_service):
        """Test full repository ingestion through GitLab RAG service"""
        # Mock the vector store
        gitlab_rag_service.vector_store_service.add_documents = AsyncMock()

        result = await gitlab_rag_service.ingest_repository(ref="main")

        assert result["success"] is True
        assert result["repository_info"] is not None
        assert result["stats"]["total_files"] > 0

    def test_gitlab_service_get_stats(self, gitlab_rag_service):
        """Test getting repository statistics"""
        gitlab_rag_service.vector_store_service.get_stats = MagicMock(
            return_value={
                "document_count": 25,
                "status": "active"
            }
        )

        stats = gitlab_rag_service.get_repository_stats()

        assert stats["total_chunks"] == 25

    def test_invalid_configuration_validation(self, gitlab_rag_service):
        """Test configuration validation with missing environment variables"""
        with patch.dict(
            'app.services.gitlab_service.os.environ',
            {},
            clear=True
        ):
            is_valid, message = gitlab_rag_service.validate_setup()

            assert is_valid is False
            assert "GITLAB_TOKEN" in message

    def test_rate_limiting_in_ingestion(self, ingestion_service):
        """Test that rate limiting is applied during ingestion"""
        import time

        # Create many files to trigger rate limiting
        many_files = [
            {
                "path": f"file{i}.py",
                "content": f"def func{i}(): pass",
                "metadata": {"file_path": f"file{i}.py", "file_size": 20}
            }
            for i in range(30)
        ]

        ingestion_service.gitlab_connector.fetch_all_code_files = MagicMock(
            return_value=many_files
        )

        with patch('app.connectors.gitlab_connector.time.sleep') as mock_sleep:
            asyncio.run(ingestion_service.ingest_repository(ref="main"))

            # Should call sleep for rate limiting
            assert mock_sleep.call_count > 0

    @pytest.mark.asyncio
    async def test_duplicate_ingestion_prevention(self, gitlab_rag_service):
        """Test that duplicate ingestion is prevented"""
        # Simulate existing chunks
        gitlab_rag_service.vector_store_service.get_stats = MagicMock(
            return_value={"document_count": 10, "status": "active"}
        )

        result = await gitlab_rag_service.ingest_repository(ref="main")

        assert result["success"] is False
        assert "already has" in result["message"]

    @pytest.mark.asyncio
    async def test_search_result_formatting(self, gitlab_rag_service):
        """Test that search results are properly formatted"""
        # Create mock result with rich metadata
        mock_node = MagicMock()
        mock_node.text = "def calculate_total(items): return sum(items)"
        mock_node.metadata = {
            "file_path": "src/math.py",
            "chunk_type": "function",
            "language": "python",
            "chunk_name": "calculate_total",
            "chunk_signature": "def calculate_total(items)",
            "start_line": 10,
            "end_line": 12,
        }

        mock_result = MagicMock()
        mock_result.node = mock_node
        mock_result.score = 0.92

        gitlab_rag_service.vector_store_service.search = AsyncMock(
            return_value=[mock_result]
        )

        result = await gitlab_rag_service.search_code(
            query="calculate sum",
            top_k=5
        )

        assert result["success"] is True
        assert len(result["results"]) == 1

        formatted = result["results"][0]
        assert formatted["text"] == mock_node.text
        assert formatted["score"] == 0.92
        assert formatted["file_path"] == "src/math.py"
        assert formatted["chunk_name"] == "calculate_total"
        assert formatted["start_line"] == 10
        assert formatted["end_line"] == 12

    def test_chunk_hierarchy_preserved(self, ingestion_service):
        """Test that chunk hierarchy is preserved"""
        python_code = '''
class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        return self.db.query("SELECT * FROM users WHERE id = ?", user_id)
'''

        chunks = ingestion_service.ast_splitter.split_file(python_code, "service.py")

        # Find class and its methods
        class_chunks = [c for c in chunks if c.type == "class" and c.name == "UserService"]
        method_chunks = [c for c in chunks if c.type == "method"]

        assert len(class_chunks) == 1
        assert len(method_chunks) == 2  # __init__, get_user

        # Methods should reference parent class
        for method in method_chunks:
            assert method.parent_class == "UserService"

    @pytest.mark.asyncio
    async def test_clear_all_code(self, gitlab_rag_service):
        """Test clearing all code documents"""
        gitlab_rag_service.get_repository_stats = MagicMock(
            return_value={
                "total_chunks": 15,
                "total_files": 4,
            }
        )

        result = gitlab_rag_service.clear_all_code()

        assert result["success"] is True
        assert result["cleared_chunks"] == 15

    def test_gitlab_connector_singleton(self):
        """Test GitLab connector singleton pattern"""
        from app.connectors.gitlab_connector import (
            get_gitlab_connector,
            _connector_instance
        )

        # Reset singleton
        import app.connectors.gitlab_connector as module
        module._connector_instance = None

        with patch.dict(
            'app.connectors.gitlab_connector.os.environ',
            {'GITLAB_TOKEN': 'test', 'GITLAB_PROJECT_ID': '123'}
        ), patch('app.connectors.gitlab_connector.gitlab.Gitlab'):
            connector1 = get_gitlab_connector()
            connector2 = get_gitlab_connector()

            assert connector1 is connector2  # Same instance

    def test_code_ingestion_service_singleton(self):
        """Test code ingestion service singleton pattern"""
        from app.rag.code_ingestion import (
            get_code_ingestion_service,
            _service_instance
        )

        # Reset singleton
        import app.rag.code_ingestion as module
        module._service_instance = None

        with patch.dict(
            'app.connectors.gitlab_connector.os.environ',
            {'GITLAB_TOKEN': 'test', 'GITLAB_PROJECT_ID': '123'}
        ), patch('app.connectors.gitlab_connector.gitlab.Gitlab'):
            service1 = get_code_ingestion_service()
            service2 = get_code_ingestion_service()

            assert service1 is service2  # Same instance
