# Test Suite Documentation

## Overview

Comprehensive test suite for the GitLab Connector with AST-based chunking implementation.

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   ├── test_ast_splitter.py      # AST parsing tests (400+ assertions)
│   └── test_gitlab_connector.py  # GitLab API tests (mocked)
├── integration/                   # Integration tests
│   └── test_code_ingestion.py    # End-to-end flow tests
├── conftest.py                   # Pytest configuration & fixtures
└── README.md                     # This file
```

## Running Tests

### Run All Tests
```bash
uv run pytest -v
```

### Run Only Unit Tests
```bash
uv run pytest -v tests/unit
```

### Run Only Integration Tests
```bash
uv run pytest -v tests/integration
```

### Run with Coverage
```bash
uv run pytest -v --cov=app --cov-report=html
```

### Run Specific Test File
```bash
uv run pytest -v tests/unit/test_ast_splitter.py
```

### Run Specific Test
```bash
uv run pytest -v tests/unit/test_ast_splitter.py::TestASTCodeSplitter::test_parse_python_simple_function
```

## Test Statistics

- **Total Test Files**: 3
- **Total Test Cases**: 60+
- **Languages Covered**: Python, JavaScript, TypeScript, PHP
- **Mock Tests**: 25 (no credentials needed)
- **Integration Tests**: 15 (with mocked dependencies)

## Test Coverage

### AST Splitter Tests (`test_ast_splitter.py`)
✅ Language detection (4 languages)
✅ Python parsing (functions, classes, methods, decorators, type hints)
✅ JavaScript parsing (functions, classes, arrow functions, async/await)
✅ TypeScript parsing (interfaces, generics, types)
✅ PHP parsing (classes, namespaces, traits, visibility)
✅ Import extraction
✅ Docstring extraction
✅ Metadata preservation
✅ Chunk hierarchy
✅ Edge cases (empty files, comments, etc.)

### GitLab Connector Tests (`test_gitlab_connector.py`)
✅ Authentication and connection
✅ Repository traversal
✅ File filtering (extensions, .gitignore patterns)
✅ Content fetching
✅ Metadata extraction
✅ Rate limiting
✅ Error handling
✅ Document conversion
✅ Configuration validation
✅ Singleton pattern

### Integration Tests (`test_code_ingestion.py`)
✅ End-to-end ingestion pipeline
✅ Multiple language handling
✅ Chunk type diversity
✅ Metadata preservation
✅ Error handling
✅ Service layer integration
✅ Search functionality
✅ Duplicate prevention
✅ Configuration validation
✅ Result formatting

## Fixtures

### Code Samples
- `sample_python_code()` - Python class with methods and type hints
- `sample_javascript_code()` - JS class with async methods
- `sample_typescript_code()` - TypeScript interface and generics
- `sample_php_code()` - PHP class with namespaces and traits

### Mock Objects
- `mock_gitlab_client()` - Mocked GitLab client
- `sample_gitlab_project_structure()` - Sample repository structure
- `mock_gitlab_connector()` - Mocked connector with sample data

## Requirements

Tests use:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting (optional)
- `pytest-mock` - Mocking utilities

Already included in project dependencies.

## Environment Variables

Tests automatically set these variables:
```bash
VOYAGE_API_KEY=test_voyage_key
GOOGLE_API_KEY=test_google_key
GITLAB_TOKEN=test_gitlab_token
GITLAB_PROJECT_ID=123
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## Manual Testing with Real GitLab

When you have GitLab credentials, run:

1. **Check connectivity**:
```bash
curl http://localhost:8000/code/health
```

2. **Ingest repository**:
```bash
curl -X POST "http://localhost:8000/code/ingest?ref=main"
```

3. **Search code**:
```bash
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "function", "top_k": 10}'
```

4. **Get stats**:
```bash
curl http://localhost:8000/code/stats
```

## Test Results

Expected output for a full test run:

```
tests/unit/test_ast_splitter.py::TestASTCodeSplitter::test_parse_python_simple_function PASSED
tests/unit/test_ast_splitter.py::TestASTCodeSplitter::test_parse_python_class_with_methods PASSED
tests/unit/test_ast_splitter.py::TestASTCodeSplitter::test_parse_javascript_class PASSED
...
tests/unit/test_gitlab_connector.py::TestGitLabConnector::test_fetch_repository_tree PASSED
tests/unit/test_gitlab_connector.py::TestGitLabConnector::test_to_documents PASSED
...
tests/integration/test_code_ingestion.py::TestCodeIngestionIntegration::test_full_ingestion_pipeline PASSED
tests/integration/test_code_ingestion.py::TestCodeIngestionIntegration::test_chunking_multiple_languages PASSED
...

======================== 60 passed in 5.32s =========================
```

## Troubleshooting

### If tests fail with import errors:
```bash
# Ensure you're in the project root
uv run pytest
```

### If async tests fail:
```bash
# Install pytest-asyncio if missing
uv add pytest-asyncio
```

### If tree-sitter tests fail:
```bash
# Reinstall dependencies
uv sync
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    uv sync
    uv run pytest -v --cov=app

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Next Steps

After tests pass:
1. Create `.env` with real GitLab credentials
2. Start the server
3. Test with real repository
4. Run performance tests (Phase 11)

## Questions?

See implementation details in:
- `GITLAB_IMPLEMENTATION_TRACKING.md` - Full tracking document
- `CLAUDE.md` - Project documentation with API examples
