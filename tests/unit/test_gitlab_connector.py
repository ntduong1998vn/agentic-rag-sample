"""
Unit tests for GitLab connector.

Tests the GitLabConnector class using mocks to avoid requiring real GitLab credentials.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Import the GitLab connector
from app.connectors.gitlab_connector import GitLabConnector, get_gitlab_connector


class TestGitLabConnector:
    """Test suite for GitLab connector"""

    @pytest.fixture
    def mock_gitlab(self):
        """Create a mock GitLab client"""
        with patch('app.connectors.gitlab_connector.gitlab.Gitlab') as mock_gl:
            # Mock the Gitlab client
            mock_instance = MagicMock()
            mock_gl.return_value = mock_instance

            # Mock authentication
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_instance.user = mock_user

            # Mock project
            mock_project = MagicMock()
            mock_project.id = 123
            mock_project.name = "test-project"
            mock_project.description = "Test project"
            mock_project.web_url = "https://gitlab.com/test/test-project"
            mock_project.default_branch = "main"
            mock_project.visibility = "private"
            mock_project.path_with_namespace = "test/test-project"

            mock_instance.projects.get.return_value = mock_project

            yield mock_instance

    @pytest.fixture
    def connector(self, mock_gitlab):
        """Create GitLab connector with mocked client"""
        with patch.dict(
            'app.connectors.gitlab_connector.os.environ',
            {
                'GITLAB_TOKEN': 'fake_token',
                'GITLAB_PROJECT_ID': '123'
            },
            clear=False
        ):
            yield GitLabConnector(
                gitlab_url="https://gitlab.com",
                gitlab_token="fake_token",
                project_id="123"
            )

    def test_initialization(self, connector, mock_gitlab):
        """Test connector initialization"""
        assert connector.gitlab_url == "https://gitlab.com"
        assert connector.gitlab_token == "fake_token"
        assert connector.project_id == "123"
        assert connector.gl is not None
        assert connector.project is not None

    def test_detect_code_file_python(self, connector):
        """Test code file detection for Python"""
        assert connector.is_code_file("test.py") is True
        assert connector.is_code_file("module.py") is True

    def test_detect_code_file_javascript(self, connector):
        """Test code file detection for JavaScript"""
        assert connector.is_code_file("app.js") is True
        assert connector.is_code_file("utils.js") is True

    def test_detect_code_file_typescript(self, connector):
        """Test code file detection for TypeScript"""
        assert connector.is_code_file("component.ts") is True
        assert connector.is_code_file("component.tsx") is True

    def test_detect_code_file_php(self, connector):
        """Test code file detection for PHP"""
        assert connector.is_code_file("api.php") is True
        assert connector.is_code_file("index.php") is True

    def test_not_code_file(self, connector):
        """Test non-code file detection"""
        assert connector.is_code_file("image.jpg") is False
        assert connector.is_code_file("document.pdf") is False
        assert connector.is_code_file("data.json") is False
        assert connector.is_code_file("README.md") is False

    def test_should_ignore_pattern(self, connector):
        """Test ignore pattern matching"""
        # Should ignore
        assert connector.should_ignore_path("node_modules/package/index.js") is True
        assert connector.should_ignore_path("vendor/autoload.php") is True
        assert connector.should_ignore_path("dist/bundle.min.js") is True
        assert connector.should_ignore_path("__pycache__/file.pyc") is True

        # Should not ignore
        assert connector.should_ignore_path("src/app.js") is False
        assert connector.should_ignore_path("lib/Service.php") is False

    def test_minified_files_ignored(self, connector):
        """Test that minified files are ignored"""
        assert connector.should_ignore_path("jquery.min.js") is True
        assert connector.should_ignore_path("app.bundle.js") is True

    def test_fetch_repository_tree(self, connector, mock_gitlab):
        """Test fetching repository tree"""
        # Mock repository tree response
        mock_tree = [
            {"id": "abc123", "name": "src", "type": "tree", "path": "src"},
            {"id": "def456", "name": "main.py", "type": "blob", "path": "src/main.py"},
            {"id": "ghi789", "name": "utils.js", "type": "blob", "path": "src/utils.js"},
        ]

        connector.project.repository_tree.return_value = mock_tree

        result = connector.fetch_repository_tree(ref="main")

        assert len(result) == 3
        connector.project.repository_tree.assert_called_once_with(
            path="", ref="main", recursive=True, all=True
        )

    def test_fetch_file_content_success(self, connector, mock_gitlab):
        """Test successful file content fetch"""
        import base64

        content = "def hello(): print('Hello')"
        encoded = base64.b64encode(content.encode()).decode()

        mock_file = MagicMock()
        mock_file.content = encoded
        mock_file.size = len(content)

        connector.project.files.get.return_value = mock_file

        result = connector.fetch_file_content("src/main.py", ref="main")

        assert result is not None
        assert "def hello" in result
        connector.project.files.get.assert_called_once_with(
            file_path="src/main.py", ref="main"
        )

    def test_get_project_info(self, connector):
        """Test getting project information"""
        info = connector.get_project_info()

        assert info["id"] == 123
        assert info["name"] == "test-project"
        assert "test-project" in info["web_url"]
        assert info["default_branch"] == "main"
        assert info["visibility"] == "private"

    def test_test_connection_success(self, connector, mock_gitlab):
        """Test successful connection"""
        result = connector.test_connection()
        assert result is True

    def test_test_connection_failure(self, mock_gitlab):
        """Test connection failure"""
        mock_gitlab.user.side_effect = Exception("Connection failed")

        with patch.dict(
            'app.connectors.gitlab_connector.os.environ',
            {'GITLAB_TOKEN': 'fake_token', 'GITLAB_PROJECT_ID': '123'}
        ):
            connector = GitLabConnector()
            result = connector.test_connection()

        assert result is False

    def test_fetch_all_code_files(self, connector, mock_gitlab):
        """Test fetching all code files"""
        # Mock tree
        import base64

        mock_tree = [
            {"id": "1", "name": "main.py", "type": "blob", "path": "main.py"},
            {"id": "2", "name": "utils.js", "type": "blob", "path": "utils.js"},
            {"id": "3", "name": "ignore.txt", "type": "blob", "path": "ignore.txt"},
        ]
        connector.project.repository_tree.return_value = mock_tree

        # Mock file contents
        def mock_file_get(file_path, ref=None):
            file_mock = MagicMock()
            if file_path.endswith(".py"):
                content = "def main(): pass"
            elif file_path.endswith(".js"):
                content = "function utils() {}"
            else:
                content = "not code"

            file_mock.content = base64.b64encode(content.encode()).decode()
            file_mock.size = len(content)
            return file_mock

        connector.project.files.get = mock_file_get

        result = connector.fetch_all_code_files(ref="main")

        # Should only return code files (.py and .js, not .txt)
        assert len(result) == 2
        assert all(f["path"].endswith((".py", ".js")) for f in result)

        # Verify each file has required fields
        for file_info in result:
            assert "path" in file_info
            assert "content" in file_info
            assert "metadata" in file_info

    def test_to_documents(self, connector):
        """Test converting to LlamaIndex Documents"""
        code_files = [
            {
                "path": "main.py",
                "content": "def main(): pass",
                "metadata": {
                    "file_path": "main.py",
                    "file_name": "main.py",
                    "file_size": 20,
                    "repository_name": "test-repo",
                }
            },
            {
                "path": "utils.js",
                "content": "function util() {}",
                "metadata": {
                    "file_path": "utils.js",
                    "file_name": "utils.js",
                    "file_size": 25,
                    "repository_name": "test-repo",
                }
            }
        ]

        documents = connector.to_documents(code_files)

        assert len(documents) == 2
        assert all(hasattr(d, "text") for d in documents)
        assert all(hasattr(d, "metadata") for d in documents)

        # Check first document
        assert documents[0].text == "def main(): pass"
        assert documents[0].metadata["file_path"] == "main.py"
        assert documents[0].metadata["repository_name"] == "test-repo"

    def test_environment_variables(self):
        """Test connector with environment variables"""
        with patch.dict(
            'app.connectors.gitlab_connector.os.environ',
            {
                'GITLAB_TOKEN': 'env_token',
                'GITLAB_PROJECT_ID': '456'
            },
            clear=False
        ):
            with patch('app.connectors.gitlab_connector.gitlab.Gitlab') as mock_gl:
                mock_instance = MagicMock()
                mock_gl.return_value = mock_instance

                mock_project = MagicMock()
                mock_instance.projects.get.return_value = mock_project

                connector = GitLabConnector()

                assert connector.gitlab_token == "env_token"
                assert connector.project_id == "456"

    @patch('app.connectors.gitlab_connector.os.environ.get')
    def test_validate_config_missing_token(self, mock_get):
        """Test validation with missing token"""
        mock_get.return_value = None

        from app.connectors.gitlab_connector import validate_gitlab_config
        result = validate_gitlab_config()

        assert result is False

    @patch('app.connectors.gitlab_connector.os.environ.get')
    def test_validate_config_success(self, mock_get):
        """Test validation with correct config"""
        def side_effect(key, default=None):
            if key == 'GITLAB_TOKEN':
                return 'valid_token'
            return default

        mock_get.side_effect = side_effect

        from app.connectors.gitlab_connector import validate_gitlab_config
        result = validate_gitlab_config()

        assert result is True

    def test_rate_limiting_delay(self, connector, mock_gitlab):
        """Test that rate limiting delays are applied"""
        import time

        # Create many files to trigger rate limiting
        mock_tree = [
            {"id": str(i), "name": f"file{i}.py", "type": "blob", "path": f"file{i}.py"}
            for i in range(25)  # More than 20 to trigger delay
        ]

        connector.project.repository_tree.return_value = mock_tree

        with patch('app.connectors.gitlab_connector.time.sleep') as mock_sleep:
            connector.fetch_all_code_files(ref="main")

            # Should call sleep at least once (for every 20 files)
            assert mock_sleep.call_count >= 1

    def test_fetch_file_metadata(self, connector, mock_gitlab):
        """Test fetching file metadata"""
        mock_file = MagicMock()
        mock_file.size = 1024
        mock_file.blob_id = "abc123"
        mock_file.commit_id = "def456"

        mock_commit = MagicMock()
        mock_commit.id = "def456"
        mock_commit.author_name = "Test Author"
        mock_commit.author_email = "test@example.com"
        mock_commit.authored_date = "2024-01-01T00:00:00Z"
        mock_commit.message = "Initial commit"

        connector.project.files.get.return_value = mock_file
        connector.project.commits.list.return_value = [mock_commit]

        result = connector.fetch_file_metadata("test.py", ref="main")

        assert result["file_path"] == "test.py"
        assert result["file_size"] == 1024
        assert result["blob_id"] == "abc123"
        assert result["commit_id"] == "def456"
        assert result["last_commit"]["author_name"] == "Test Author"

    def test_pagination_handling(self, connector, mock_gitlab):
        """Test pagination for large repositories"""
        # Simulate pagination by returning a large tree
        large_tree = [
            {"id": str(i), "name": f"file{i}.py", "type": "blob", "path": f"file{i}.py"}
            for i in range(150)  # Large repository
        ]

        connector.project.repository_tree.return_value = large_tree

        result = connector.fetch_all_code_files(ref="main")

        # Should fetch all files despite pagination
        assert len(result) == 150

    def test_binary_file_exclusion(self, connector, mock_gitlab):
        """Test that binary files are excluded"""
        mock_tree = [
            {"id": "1", "name": "image.jpg", "type": "blob", "path": "assets/image.jpg"},
            {"id": "2", "name": "data.json", "type": "blob", "path": "data.json"},
            {"id": "3", "name": "app.py", "type": "blob", "path": "app.py"},
        ]

        connector.project.repository_tree.return_value = mock_tree
        connector.is_code_file = lambda path: path.endswith('.py')  # Only Python is code

        result = connector.fetch_all_code_files(ref="main")

        assert len(result) == 1
        assert result[0]["path"] == "app.py"

    def test_fetch_repository_documents(self, connector, mock_gitlab):
        """Test fetching repository as documents"""
        import base64

        mock_tree = [
            {"id": "1", "name": "main.py", "type": "blob", "path": "main.py"},
        ]

        connector.project.repository_tree.return_value = mock_tree

        mock_file = MagicMock()
        mock_file.content = base64.b64encode(b"def main(): pass").decode()
        mock_file.size = 20
        connector.project.files.get.return_value = mock_file

        documents = connector.fetch_repository_documents(ref="main")

        assert len(documents) == 1
        assert isinstance(documents[0].text, str)
        assert documents[0].metadata["file_path"] == "main.py"
