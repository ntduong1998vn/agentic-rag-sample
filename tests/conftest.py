"""
Pytest configuration and shared fixtures for testing.

Contains common test utilities, fixtures, and configuration used across
the test suite.
"""

import pytest
import os
import sys
from pathlib import Path


# Add the project root to sys.path so tests can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables"""
    os.environ.setdefault('VOYAGE_API_KEY', 'test_voyage_key')
    os.environ.setdefault('GOOGLE_API_KEY', 'test_google_key')
    os.environ.setdefault('GITLAB_TOKEN', 'test_gitlab_token')
    os.environ.setdefault('GITLAB_PROJECT_ID', '123')
    os.environ.setdefault('CHROMA_HOST', 'localhost')
    os.environ.setdefault('CHROMA_PORT', '8001')
    yield


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return '''
import os
from typing import List, Dict

def process_data(data: List[str]) -> Dict[str, int]:
    """Process data and return statistics."""
    results = {}
    for item in data:
        results[item] = len(item)
    return results

class DataProcessor:
    def __init__(self, config: Dict):
        self.config = config

    def process(self, data: List[str]) -> Dict[str, int]:
        return process_data(data)
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for testing"""
    return '''
/**
 * Sort items by date
 */
function sortByDate(items) {
    return items.sort((a, b) => new Date(a.date) - new Date(b.date));
}

class DataManager {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.cache = new Map();
    }

    async fetchData(id) {
        if (this.cache.has(id)) {
            return this.cache.get(id);
        }
        const data = await fetch(`${this.apiUrl}/${id}`);
        const result = await data.json();
        this.cache.set(id, result);
        return result;
    }
}

module.exports = { sortByDate, DataManager };
'''


@pytest.fixture
def sample_typescript_code():
    """Sample TypeScript code for testing"""
    return '''
interface User {
    id: number;
    name: string;
    email: string;
}

class UserRepository {
    private users: User[] = [];

    add(user: User): void {
        this.users.push(user);
    }

    findById(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }

    getAll(): User[] {
        return [...this.users];
    }
}

export default UserRepository;
'''


@pytest.fixture
def sample_php_code():
    """Sample PHP code for testing"""
    return r'''
<?php
namespace App\\Services;

use App\\Models\\User;
use App\\Contracts\\RepositoryInterface;

/**
 * User repository
 */
class UserRepository implements RepositoryInterface
{
    private $db;
    private $cache = [];

    public function __construct($database)
    {
        $this->db = $database;
    }

    public function find($id): ?User
    {
        if (isset($this->cache[$id])) {
            return $this->cache[$id];
        }

        $user = $this->db->find('users', $id);
        $this->cache[$id] = $user;

        return $user;
    }

    private function validate(array $data): bool
    {
        return !empty($data['name']) && !empty($data['email']);
    }
}
'''


@pytest.fixture
def sample_gitlab_project_structure():
    """Sample GitLab project structure"""
    return [
        {"id": "1", "name": "src", "type": "tree", "path": "src"},
        {"id": "2", "name": "tests", "type": "tree", "path": "tests"},
        {"id": "3", "name": "README.md", "type": "blob", "path": "README.md"},
        {"id": "4", "name": "main.py", "type": "blob", "path": "src/main.py"},
        {"id": "5", "name": "utils.js", "type": "blob", "path": "src/utils.js"},
        {"id": "6", "name": "api.php", "type": "blob", "path": "src/api.php"},
        {"id": "7", "name": "models.ts", "type": "blob", "path": "src/models.ts"},
        {"id": "8", "name": "node_modules", "type": "tree", "path": "node_modules"},
        {"id": "9", "name": "vendor", "type": "tree", "path": "vendor"},
    ]


@pytest.fixture
def mock_gitlab_client():
    """Mock GitLab client fixture"""
    from unittest.mock import MagicMock
    import gitlab

    mock_gl = MagicMock()
    mock_gl.user = MagicMock()
    mock_gl.user.username = "testuser"

    mock_project = MagicMock()
    mock_project.id = 123
    mock_project.name = "test-project"
    mock_project.visibility = "private"
    mock_project.web_url = "https://gitlab.com/test/test-project"
    mock_project.default_branch = "main"
    mock_project.path_with_namespace = "test/test-project"

    mock_gl.projects.get.return_value = mock_project

    return mock_gl


@pytest.fixture
def temp_test_directory(tmp_path):
    """Create temporary test directory"""
    test_dir = tmp_path / "test_code"
    test_dir.mkdir()

    # Create sample files
    (test_dir / "main.py").write_text("def hello(): pass")
    (test_dir / "utils.js").write_text("function util() {}")
    (test_dir / "service.php").write_text("<?php function service() {} ?>")

    return test_dir


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_env: marks tests as requiring environment variables"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
