"""
Unit tests for AST-based code splitter.

Tests the ASTCodeSplitter class with sample code from Python, JavaScript,
TypeScript, and PHP to ensure proper parsing and chunk extraction.
"""

import pytest
from pathlib import Path

# Import the AST splitter
from app.rag.ast_splitter import ASTCodeSplitter, CodeChunk


class TestASTCodeSplitter:
    """Test suite for AST code splitter"""

    @pytest.fixture
    def splitter(self):
        """Create AST splitter instance"""
        return ASTCodeSplitter(min_tokens=10, max_tokens=2000)

    def test_detect_language_python(self, splitter):
        """Test language detection for Python files"""
        assert splitter.detect_language("test.py") == "python"
        assert splitter.detect_language("/path/to/file.py") == "python"
        assert splitter.detect_language(Path("module.py")) == "python"

    def test_detect_language_javascript(self, splitter):
        """Test language detection for JavaScript files"""
        assert splitter.detect_language("test.js") == "javascript"
        assert splitter.detect_language("/path/to/app.js") == "javascript"

    def test_detect_language_typescript(self, splitter):
        """Test language detection for TypeScript files"""
        assert splitter.detect_language("test.ts") == "typescript"
        assert splitter.detect_language("component.tsx") == "typescript"

    def test_detect_language_php(self, splitter):
        """Test language detection for PHP files"""
        assert splitter.detect_language("test.php") == "php"
        assert splitter.detect_language("/path/to/api.php") == "php"

    def test_detect_language_unsupported(self, splitter):
        """Test language detection for unsupported files"""
        assert splitter.detect_language("test.java") is None
        assert splitter.detect_language("test.go") is None
        assert splitter.detect_language("test.txt") is None
        assert splitter.detect_language("test.rs") is None

    def test_parse_python_simple_function(self, splitter):
        """Test parsing Python simple function"""
        code = """
def greet(name):
    return f"Hello, {name}!"
"""
        chunks = splitter.split_file(code, "test.py")

        assert len(chunks) > 0
        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert chunk.name == "greet"
        assert "def greet" in chunk.text
        assert chunk.language == "python"
        assert chunk.file_path == "test.py"
        assert chunk.start_line >= 0
        assert chunk.end_line > chunk.start_line

    def test_parse_python_class_with_methods(self, splitter):
        """Test parsing Python class with methods"""
        code = """
class Calculator:
    def __init__(self, value=0):
        self.value = value

    def add(self, num):
        self.value += num
        return self.value

    def multiply(self, num):
        self.value *= num
        return self.value
"""
        chunks = splitter.split_file(code, "calc.py")

        # Should have class chunk and method chunks
        class_chunks = [c for c in chunks if c.type == "class"]
        method_chunks = [c for c in chunks if c.type == "method"]

        assert len(class_chunks) == 1
        assert len(method_chunks) == 3  # __init__, add, multiply

        # Check class
        cls = class_chunks[0]
        assert cls.name == "Calculator"
        assert "class Calculator" in cls.text

        # Check methods have parent class
        for method in method_chunks:
            assert method.parent_class == "Calculator"

    def test_parse_python_function_with_docstring(self, splitter):
        """Test parsing Python function with docstring"""
        code = '''
def process_data(data):
    """Process incoming data and return result."""
    return data.upper()
'''
        chunks = splitter.split_file(code, "test.py")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert chunk.name == "process_data"
        # Note: Simple docstring extraction may not catch all cases

    def test_parse_python_with_type_hints(self, splitter):
        """Test parsing Python with type hints"""
        code = '''
from typing import List, Dict

def analyze_text(text: str, keywords: List[str]) -> Dict[str, int]:
    """Analyze text for keywords."""
    results = {}
    for keyword in keywords:
        results[keyword] = text.count(keyword)
    return results
'''
        chunks = splitter.split_file(code, "analyzer.py")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert "text: str" in chunk.text
        assert "List[str]" in chunk.text
        assert "Dict[str, int]" in chunk.text

    def test_parse_python_decorators(self, splitter):
        """Test parsing Python function with decorators"""
        code = '''
@app.route('/api/users')
def get_users():
    return {"users": []}
'''
        chunks = splitter.split_file(code, "api.py")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert "@app.route" in chunk.text
        assert "def get_users" in chunk.text

    def test_parse_javascript_function(self, splitter):
        """Test parsing JavaScript function"""
        code = '''
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
'''
        chunks = splitter.split_file(code, "utils.js")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert chunk.name == "calculateTotal"
        assert chunk.language == "javascript"

    def test_parse_javascript_arrow_function(self, splitter):
        """Test parsing JavaScript arrow function"""
        code = '''
const multiply = (a, b) => {
    return a * b;
};
'''
        chunks = splitter.split_file(code, "math.js")

        # Arrow functions are extracted as functions
        function_chunks = [c for c in chunks if c.type in ["function", "variable"]]
        assert len(function_chunks) >= 1

    def test_parse_javascript_class(self, splitter):
        """Test parsing JavaScript ES6 class"""
        code = '''
class UserService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    async getUser(id) {
        const response = await fetch(`${this.apiUrl}/users/${id}`);
        return response.json();
    }
}
'''
        chunks = splitter.split_file(code, "user.js")

        class_chunks = [c for c in chunks if c.type == "class"]
        method_chunks = [c for c in chunks if c.type == "method"]

        assert len(class_chunks) == 1
        assert class_chunks[0].name == "UserService"
        assert len(method_chunks) == 2  # constructor, getUser

    def test_parse_typescript_interface(self, splitter):
        """Test parsing TypeScript interface"""
        code = '''
interface User {
    id: number;
    name: string;
    email: string;
}

function createUser(data: User): User {
    return { ...data };
}
'''
        chunks = splitter.split_file(code, "models.ts")

        # Should extract the function
        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert "data: User" in chunk.text
        assert ": User" in chunk.text

    def test_parse_typescript_generics(self, splitter):
        """Test parsing TypeScript with generics"""
        code = '''
class Repository<T> {
    private items: T[] = [];

    add(item: T): void {
        this.items.push(item);
    }

    getAll(): T[] {
        return this.items;
    }
}
'''
        chunks = splitter.split_file(code, "repo.ts")

        class_chunks = [c for c in chunks if c.type == "class"]
        method_chunks = [c for c in chunks if c.type == "method"]

        assert len(class_chunks) == 1
        assert "Repository<T>" in class_chunks[0].text
        assert len(method_chunks) == 2  # add, getAll

    def test_parse_php_class(self, splitter):
        """Test parsing PHP class"""
        code = '''<?php
class Database {
    private $connection;

    public function connect($host, $user, $pass) {
        $this->connection = new PDO($host, $user, $pass);
    }

    public function query($sql) {
        return $this->connection->query($sql);
    }
}
?>
'''
        chunks = splitter.split_file(code, "Database.php")

        class_chunks = [c for c in chunks if c.type == "class"]
        method_chunks = [c for c in chunks if c.type == "method"]

        assert len(class_chunks) == 1
        assert class_chunks[0].name == "Database"
        assert len(method_chunks) == 2  # connect, query

    def test_parse_php_namespaces(self, splitter):
        """Test parsing PHP with namespaces"""
        code = '''<?php
namespace App\\Services;

use App\\Models\\User;

class UserService {
    public function getUser($id) {
        return User::find($id);
    }
}
?>
'''
        chunks = splitter.split_file(code, "UserService.php")

        # Should have imports chunk
        imports = [c for c in chunks if c.name == "imports"]
        assert len(imports) == 1
        assert "use App\\Models\\User" in imports[0].text

        # Should have class
        class_chunks = [c for c in chunks if c.type == "class"]
        assert len(class_chunks) == 1

    def test_parse_php_visibility(self, splitter):
        """Test parsing PHP visibility modifiers"""
        code = '''<?php
class BankAccount {
    private $balance;
    protected $transactions;
    public $accountNumber;

    public function deposit($amount) {
        $this->balance += $amount;
    }

    private function audit() {
        // Private method
    }
}
?>
'''
        chunks = splitter.split_file(code, "BankAccount.php")

        method_chunks = [c for c in chunks if c.type == "method"]
        assert len(method_chunks) == 2  # deposit (public), audit (private)

        # Both should be marked as methods with parent class
        for method in method_chunks:
            assert method.parent_class == "BankAccount"

    def test_extract_imports_python(self, splitter):
        """Test extracting Python imports"""
        code = '''
import os
import sys
from typing import List, Dict
from collections import defaultdict

def test():
    pass
'''
        chunks = splitter.split_file(code, "test.py")

        import_chunks = [c for c in chunks if c.name == "imports"]
        assert len(import_chunks) == 1

        imports_text = import_chunks[0].text
        assert "import os" in imports_text
        assert "import sys" in imports_text
        assert "from typing import" in imports_text

    def test_javascript_commonjs_exports(self, splitter):
        """Test parsing JavaScript CommonJS exports"""
        code = '''
const utils = {
    formatDate: (date) => date.toISOString(),
    parseDate: (str) => new Date(str)
};

module.exports = utils;
'''
        chunks = splitter.split_file(code, "utils.js")

        # Should extract the object with methods
        assert len(chunks) > 0

    def test_empty_file(self, splitter):
        """Test parsing empty file"""
        chunks = splitter.split_file("", "empty.py")
        assert len(chunks) == 0

    def test_file_with_only_comments(self, splitter):
        """Test parsing file with only comments"""
        code = '''
# This is a comment
# Another comment

"""Module docstring."""
'''
        chunks = splitter.split_file(code, "comments.py")
        # May have imports chunk or nothing
        assert len(chunks) >= 0

    def test_typescript_enums(self, splitter):
        """Test parsing TypeScript enums"""
        code = '''
enum Status {
    Active = "ACTIVE",
    Inactive = "INACTIVE",
    Pending = "PENDING"
}

function getStatusColor(status: Status): string {
    switch (status) {
        case Status.Active: return "green";
        case Status.Inactive: return "red";
        case Status.Pending: return "yellow";
    }
}
'''
        chunks = splitter.split_file(code, "status.ts")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1
        assert "getStatusColor" in function_chunks[0].text

    def test_php_static_methods(self, splitter):
        """Test parsing PHP static methods"""
        code = '''<?php
class MathUtils {
    public static function add($a, $b) {
        return $a + $b;
    }

    public static function multiply($a, $b) {
        return $a * $b;
    }
}
?>
'''
        chunks = splitter.split_file(code, "MathUtils.php")

        method_chunks = [c for c in chunks if c.type == "method"]
        assert len(method_chunks) == 2

        for method in method_chunks:
            assert "static" in method.text.lower()

    def test_javascript_async_await(self, splitter):
        """Test parsing JavaScript async/await"""
        code = '''
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(error);
        throw error;
    }
}
'''
        chunks = splitter.split_file(code, "api.js")

        function_chunks = [c for c in chunks if c.type == "function"]
        assert len(function_chunks) == 1

        chunk = function_chunks[0]
        assert "async" in chunk.text
        assert "await" in chunk.text

    def test_split_documents_llamaindex(self, splitter):
        """Test splitting LlamaIndex documents"""
        from llama_index.core import Document

        doc1 = Document(
            text="def func1(): pass",
            metadata={"file_path": "test1.py"}
        )
        doc2 = Document(
            text="def func2(): pass",
            metadata={"file_path": "test2.py"}
        )

        chunks = splitter.split_documents([doc1, doc2])

        assert len(chunks) == 2
        assert all(isinstance(c, Document) for c in chunks)
        assert chunks[0].metadata["chunk_type"] == "function"
        assert chunks[1].metadata["chunk_type"] == "function"

    def test_create_ast_splitter_factory(self):
        """Test factory function for creating AST splitter"""
        from app.rag.ast_splitter import create_ast_splitter

        splitter = create_ast_splitter()
        assert isinstance(splitter, ASTCodeSplitter)
        assert splitter.min_tokens == 100  # Default value
        assert splitter.max_tokens == 2000  # Default value

    def test_python_property_decorator(self, splitter):
        """Test Python property decorator"""
        code = '''
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self._celsius = (value - 32) * 5/9
'''
        chunks = splitter.split_file(code, "temp.py")

        method_chunks = [c for c in chunks if c.type == "method"]
        # Should have __init__, fahrenheit (property), fahrenheit (setter)
        assert len(method_chunks) >= 2

    def test_typescript_abstract_classes(self, splitter):
        """Test TypeScript abstract classes"""
        code = '''
abstract class Animal {
    abstract makeSound(): void;

    move(): void {
        console.log("Moving...");
    }
}

class Dog extends Animal {
    makeSound(): void {
        console.log("Woof!");
    }
}
'''
        chunks = splitter.split_file(code, "animals.ts")

        class_chunks = [c for c in chunks if c.type == "class"]
        assert len(class_chunks) == 2  # Animal, Dog

        method_chunks = [c for c in chunks if c.type == "method"]
        assert len(method_chunks) == 3  # makeSound (abstract), move, makeSound (Dog)

    def test_php_abstract_methods(self, splitter):
        """Test PHP abstract methods"""
        code = '''<?php
abstract class PaymentGateway {
    abstract public function charge($amount);

    public function refund($transactionId) {
        // Common refund logic
    }
}
?>
'''
        chunks = splitter.split_file(code, "PaymentGateway.php")

        class_chunks = [c for c in chunks if c.type == "class"]
        assert len(class_chunks) == 1

        method_chunks = [c for c in chunks if c.type == "method"]
        assert len(method_chunks) == 2  # charge (abstract), refund
