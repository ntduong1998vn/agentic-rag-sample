"""
AST-based code splitter for multiple programming languages using LangChain.

This module provides a service for parsing code files using tree-sitter
and extracting structured chunks at file, class, and function levels.
Supports Python, JavaScript, TypeScript, and PHP.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import logging
from dataclasses import dataclass

# Tree-sitter imports
from tree_sitter import Language, Parser, Tree, Node

# LangChain imports
from langchain_core.documents import Document

# Local imports
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)


@dataclass
class CodeChunk:
    """Represents a code chunk with metadata"""
    text: str
    type: str  # 'file', 'class', 'function', 'method'
    language: str
    file_path: str
    start_line: int
    end_line: int
    name: Optional[str] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_class: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ASTCodeSplitter:
    """
    AST-based code splitter supporting Python, JavaScript, TypeScript, and PHP.
    Extracts structured chunks at file, class, and function levels.
    """

    # Supported languages and their file extensions
    SUPPORTED_LANGUAGES = {
        'python': ['.py'],
        'javascript': ['.js'],
        'typescript': ['.ts', '.tsx'],
        'php': ['.php'],
    }

    # Tree-sitter language libraries
    LANGUAGE_LIBS = {
        'python': 'tree_sitter_python',
        'javascript': 'tree_sitter_javascript',
        'typescript': 'tree_sitter_typescript',
        'php': 'tree_sitter_php',
    }

    def __init__(self, min_tokens: int = 100, max_tokens: int = 2000):
        """
        Initialize the AST code splitter.

        Args:
            min_tokens: Minimum tokens per chunk
            max_tokens: Maximum tokens per chunk
        """
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.parsers = {}
        self._initialize_parsers()
        logger.info(f"Initialized ASTCodeSplitter for {len(self.parsers)} languages")

    def _initialize_parsers(self) -> None:
        """Initialize tree-sitter parsers for all supported languages"""
        for lang_name in self.SUPPORTED_LANGUAGES.keys():
            try:
                # Import the language library
                lang_module = __import__(self.LANGUAGE_LIBS[lang_name])

                # Different language packages have different attribute names
                if lang_name == 'typescript':
                    # tree_sitter_typescript provides both tsx and typescript
                    # We use typescript as default, tsx for tsx files when parsing
                    language_func = lang_module.language_typescript
                elif lang_name == 'php':
                    # tree_sitter_php provides language_php or language_php_only
                    language_func = lang_module.language_php
                else:
                    # tree_sitter_python and tree_sitter_javascript use language()
                    language_func = lang_module.language

                language = Language(language_func())

                # Create parser with language (new API for tree-sitter 0.21.0+)
                parser = Parser(language)
                self.parsers[lang_name] = parser

                logger.debug(f"Initialized tree-sitter parser for {lang_name}")
            except Exception as e:
                logger.error(f"Failed to initialize parser for {lang_name}: {str(e)}")
                raise

    def detect_language(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Detect programming language from file path.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if not supported
        """
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()

        for lang_name, extensions in self.SUPPORTED_LANGUAGES.items():
            if file_ext in extensions:
                return lang_name

        logger.warning(f"Unsupported file extension: {file_ext}")
        return None

    def parse_code(self, code: str, language: str) -> Optional[Tree]:
        """
        Parse code using tree-sitter for the given language.

        Args:
            code: Source code as string
            language: Language name

        Returns:
            Parsed tree or None on error
        """
        parser = self.parsers.get(language)
        if not parser:
            logger.error(f"No parser available for language: {language}")
            return None

        try:
            tree = parser.parse(code.encode('utf-8'))
            return tree
        except Exception as e:
            logger.error(f"Failed to parse code: {str(e)}")
            return None

    def extract_docstring(self, node: Node, code: str, language: str) -> Optional[str]:
        """
        Extract docstring/comments from a node.

        Args:
            node: AST node
            code: Full source code
            language: Language name

        Returns:
            Docstring text or None
        """
        try:
            if language == 'python':
                return self._extract_python_docstring(node, code)
            elif language in ['javascript', 'typescript']:
                return self._extract_js_docstring(node, code)
            elif language == 'php':
                return self._extract_php_docstring(node, code)
        except Exception as e:
            logger.debug(f"Failed to extract docstring: {str(e)}")

        return None

    def _extract_python_docstring(self, node: Node, code: str) -> Optional[str]:
        """Extract Python docstring (first string after definition)"""
        # Look for a string node as first child or sibling
        for child in node.children:
            if child.type == 'string':
                return self._node_text(child, code).strip('"\' ')

        # Check next sibling
        next_sibling = node.next_named_sibling
        if next_sibling and next_sibling.type == 'expression_statement':
            str_child = next_sibling.child_by_field_name('value')
            if str_child and str_child.type == 'string':
                return self._node_text(str_child, code).strip('"\' ')

        return None

    def _extract_js_docstring(self, node: Node, code: str) -> Optional[str]:
        """Extract JavaScript/TypeScript JSDoc comment"""
        # Check previous sibling for JSDoc
        prev_sibling = node.prev_named_sibling
        if prev_sibling and prev_sibling.type in ['comment', 'line_comment', 'block_comment']:
            comment_text = self._node_text(prev_sibling, code)
            if comment_text.startswith('/**') or comment_text.startswith('/*'):
                return comment_text

        return None

    def _extract_php_docstring(self, node: Node, code: str) -> Optional[str]:
        """Extract PHPDoc comment"""
        # Check previous sibling for PHPDoc
        prev_sibling = node.prev_named_sibling
        if prev_sibling and prev_sibling.type in ['comment', 'phpdoc']:
            comment_text = self._node_text(prev_sibling, code)
            if comment_text.startswith('/**'):
                return comment_text

        return None

    def _node_text(self, node: Node, code: str) -> str:
        """Extract text from a node"""
        return code[node.start_byte:node.end_byte]

    def extract_function_chunks(self, tree: Tree, code: str, language: str,
                               file_path: str) -> List[CodeChunk]:
        """
        Extract function/method chunks from the AST.

        Args:
            tree: Parsed AST tree
            code: Source code
            language: Language name
            file_path: File path

        Returns:
            List of function chunks
        """
        chunks = []

        if language == 'python':
            chunks.extend(self._extract_python_functions(tree, code, file_path))
        elif language in ['javascript', 'typescript']:
            chunks.extend(self._extract_js_functions(tree, code, file_path, language))
        elif language == 'php':
            chunks.extend(self._extract_php_functions(tree, code, file_path))

        return chunks

    def _extract_python_functions(self, tree: Tree, code: str,
                                 file_path: str) -> List[CodeChunk]:
        """Extract Python function definitions"""
        chunks = []

        def traverse(node: Node, parent_class: Optional[str] = None):
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    start_line = node.start_point[0]
                    end_line = node.end_point[0]

                    # Extract decorators first to adjust start line
                    decorators = self._extract_python_decorators(node, code)
                    if decorators:
                        # Find the earliest decorator to adjust start_line
                        prev_sibling = node.prev_named_sibling
                        while prev_sibling and prev_sibling.type == 'decorator':
                            start_line = prev_sibling.start_point[0]
                            prev_sibling = prev_sibling.prev_named_sibling

                    # Get signature (first line after decorators)
                    chunk_text = self._get_node_text_with_decorators(node, code)
                    function_lines = chunk_text.split('\n')
                    # Find the first non-decorator line for signature
                    signature_line = ''
                    for line in function_lines:
                        if line.strip() and not line.strip().startswith('@'):
                            signature_line = line
                            break

                    # Extract docstring
                    docstring = self.extract_docstring(node, code, 'python')

                    chunk = CodeChunk(
                        text=chunk_text,
                        type='method' if parent_class else 'function',
                        language='python',
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        name=name,
                        signature=signature_line,
                        docstring=docstring,
                        parent_class=parent_class,
                        metadata={
                            'parameters': self._extract_python_params(node, code),
                            'return_type': self._extract_python_return_type(node, code),
                            'decorators': decorators,
                        }
                    )
                    chunks.append(chunk)

            elif node.type == 'class_definition':
                # For methods, track parent class
                name_node = node.child_by_field_name('name')
                if name_node:
                    parent_class = self._node_text(name_node, code)
                    for child in node.children:
                        traverse(child, parent_class)
                else:
                    for child in node.children:
                        traverse(child, parent_class)
            else:
                for child in node.children:
                    traverse(child, parent_class)

        traverse(tree.root_node)
        return chunks

    def _extract_python_params(self, node: Node, code: str) -> List[str]:
        """Extract Python function parameters"""
        params_node = node.child_by_field_name('parameters')
        if params_node:
            param_nodes = params_node.children
            params = []
            for param in param_nodes:
                if param.type in ['identifier', 'typed_parameter', 'default_parameter']:
                    params.append(self._node_text(param, code))
            return params
        return []

    def _extract_python_return_type(self, node: Node, code: str) -> Optional[str]:
        """Extract Python return type annotation"""
        return_node = node.child_by_field_name('return_type')
        if return_node:
            return self._node_text(return_node, code)
        return None

    def _extract_python_decorators(self, node: Node, code: str) -> List[str]:
        """Extract Python function decorators"""
        decorators = []
        # Check if decorators are siblings before the function
        prev_sibling = node.prev_named_sibling
        while prev_sibling and prev_sibling.type == 'decorator':
            decorators.insert(0, self._node_text(prev_sibling, code))
            prev_sibling = prev_sibling.prev_named_sibling

        # Also check children of the node (some tree-sitter versions)
        if not decorators:
            for child in node.children:
                if child.type == 'decorator':
                    decorators.append(self._node_text(child, code))

        return decorators

    def _get_node_text_with_decorators(self, node: Node, code: str) -> str:
        """Get node text including any decorators before it"""
        # Get decorators
        decorators = self._extract_python_decorators(node, code)

        if decorators:
            # Combine decorators with function
            decorator_text = '\n'.join(decorators)
            function_text = self._node_text(node, code)
            return f"{decorator_text}\n{function_text}"
        else:
            return self._node_text(node, code)

    def _extract_js_functions(self, tree: Tree, code: str, file_path: str,
                             language: str) -> List[CodeChunk]:
        """Extract JavaScript/TypeScript function definitions"""
        chunks = []

        def traverse(node: Node, parent_class: Optional[str] = None):
            # Function declaration: function name() {}
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    chunk = self._create_js_chunk(node, code, file_path, language,
                                                   name, 'function', parent_class)
                    chunks.append(chunk)

            # Method definition in class: method() {}
            elif node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    chunk = self._create_js_chunk(node, code, file_path, language,
                                                   name, 'method', parent_class)
                    chunks.append(chunk)

            # Abstract method in TypeScript
            elif node.type == 'abstract_method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    chunk = self._create_js_chunk(node, code, file_path, language,
                                                   name, 'method', parent_class)
                    chunks.append(chunk)

            # Arrow function
            elif node.type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                value_node = node.child_by_field_name('value')
                if name_node and value_node and value_node.type == 'arrow_function':
                    name = self._node_text(name_node, code)
                    chunk = self._create_js_chunk(value_node, code, file_path, language,
                                                   name, 'function', parent_class)
                    chunks.append(chunk)

            # Class (for tracking parent)
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    parent_class = self._node_text(name_node, code)

            # Traverse children
            for child in node.children:
                traverse(child, parent_class)

        traverse(tree.root_node)
        return chunks

    def _create_js_chunk(self, node: Node, code: str, file_path: str,
                        language: str, name: str, chunk_type: str,
                        parent_class: Optional[str] = None) -> CodeChunk:
        """Create a JavaScript/TypeScript chunk"""
        # Get signature (first line)
        function_lines = self._node_text(node, code).split('\n')
        signature = function_lines[0] if function_lines else ''

        # Extract JSDoc
        docstring = self.extract_docstring(node, code, language)

        return CodeChunk(
            text=self._node_text(node, code),
            type=chunk_type,
            language=language,
            file_path=file_path,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            name=name,
            signature=signature,
            docstring=docstring,
            parent_class=parent_class,
            metadata={
                'parameters': self._extract_js_params(node, code),
                'async': self._is_async(node),
                'generator': self._is_generator(node),
            }
        )

    def _extract_js_params(self, node: Node, code: str) -> List[str]:
        """Extract JavaScript/TypeScript function parameters"""
        params_node = node.child_by_field_name('parameters')
        if params_node:
            param_nodes = params_node.children
            params = []
            for param in param_nodes:
                if param.type in ['identifier', 'required_parameter']:
                    params.append(self._node_text(param, code))
            return params
        return []

    def _is_async(self, node: Node) -> bool:
        """Check if function is async"""
        for child in node.children:
            if child.type == 'async':
                return True
        return False

    def _is_generator(self, node: Node) -> bool:
        """Check if function is a generator (has *)"""
        for child in node.children:
            if child.type == '*':
                return True
        return False

    def _extract_php_functions(self, tree: Tree, code: str,
                              file_path: str) -> List[CodeChunk]:
        """Extract PHP function and method definitions"""
        chunks = []

        def traverse(node: Node, parent_class: Optional[str] = None):
            # Function definition
            if node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    chunk = self._create_php_chunk(node, code, file_path, name,
                                                   'function', parent_class)
                    chunks.append(chunk)

            # Method definition
            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    chunk = self._create_php_chunk(node, code, file_path, name,
                                                   'method', parent_class)
                    chunks.append(chunk)

            # Class (for tracking parent)
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    parent_class = self._node_text(name_node, code)

            # Traverse children
            for child in node.children:
                traverse(child, parent_class)

        traverse(tree.root_node)
        return chunks

    def _create_php_chunk(self, node: Node, code: str, file_path: str,
                         name: str, chunk_type: str,
                         parent_class: Optional[str] = None) -> CodeChunk:
        """Create a PHP chunk"""
        # Get signature (first line)
        function_lines = self._node_text(node, code).split('\n')
        signature = function_lines[0] if function_lines else ''

        # Extract PHPDoc
        docstring = self.extract_docstring(node, code, 'php')

        return CodeChunk(
            text=self._node_text(node, code),
            type=chunk_type,
            language='php',
            file_path=file_path,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            name=name,
            signature=signature,
            docstring=docstring,
            parent_class=parent_class,
            metadata={
                'parameters': self._extract_php_params(node, code),
                'visibility': self._extract_php_visibility(node),
                'static': self._is_static(node),
            }
        )

    def _extract_php_params(self, node: Node, code: str) -> List[str]:
        """Extract PHP function parameters"""
        params_node = node.child_by_field_name('parameters')
        if params_node:
            param_nodes = params_node.children
            params = []
            for param in param_nodes:
                if param.type == 'simple_parameter':
                    params.append(self._node_text(param, code))
            return params
        return []

    def _extract_php_visibility(self, node: Node) -> Optional[str]:
        """Extract PHP visibility modifier (public, private, protected)"""
        for child in node.children:
            if child.type in ['public', 'private', 'protected']:
                return child.type
        return 'public'  # Default

    def _is_static(self, node: Node) -> bool:
        """Check if PHP method is static"""
        for child in node.children:
            if child.type == 'static':
                return True
        return False

    def extract_class_chunks(self, tree: Tree, code: str, language: str,
                           file_path: str) -> List[CodeChunk]:
        """
        Extract class definitions from the AST.

        Args:
            tree: Parsed AST tree
            code: Source code
            language: Language name
            file_path: File path

        Returns:
            List of class chunks
        """
        chunks = []
        root_node = tree.root_node

        def traverse(node: Node):
            if node.type in ['class_definition', 'class_declaration', 'abstract_class_declaration']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = self._node_text(name_node, code)
                    docstring = self.extract_docstring(node, code, language)

                    # Extract inheritance
                    superclasses = []
                    if language == 'python':
                        for child in node.children:
                            if child.type == 'argument_list':
                                for arg in child.children:
                                    if arg.type == 'identifier':
                                        superclasses.append(self._node_text(arg, code))
                    elif language in ['javascript', 'typescript']:
                        super_node = node.child_by_field_name('superclass')
                        if super_node:
                            superclasses.append(self._node_text(super_node, code))

                    chunk = CodeChunk(
                        text=self._node_text(node, code),
                        type='class',
                        language=language,
                        file_path=file_path,
                        start_line=node.start_point[0],
                        end_line=node.end_point[0],
                        name=name,
                        signature=self._node_text(node, code).split('\n')[0],
                        docstring=docstring,
                        metadata={
                            'superclasses': superclasses,
                            'methods_count': self._count_methods(node),
                        }
                    )
                    chunks.append(chunk)

            # Traverse children
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return chunks

    def _count_methods(self, class_node: Node) -> int:
        """Count methods in a class"""
        count = 0
        for child in class_node.children:
            if child.type in ['function_definition', 'method_definition', 'method_declaration']:
                count += 1
        return count

    def extract_imports(self, tree: Tree, code: str, language: str,
                       file_path: str) -> CodeChunk:
        """
        Extract import statements as a file-level overview chunk.

        Args:
            tree: Parsed AST tree
            code: Source code
            language: Language name
            file_path: File path

        Returns:
            Import chunk or None
        """
        imports = []
        root_node = tree.root_node

        def collect_imports(node: Node):
            # Python imports
            if node.type in ['import_statement', 'import_from_statement']:
                imports.append(self._node_text(node, code))
            # JS/TS imports
            elif node.type == 'import_statement':
                imports.append(self._node_text(node, code))
            # PHP namespace and use statements
            elif node.type in ['use_declaration', 'namespace_definition', 'namespace_use_declaration']:
                imports.append(self._node_text(node, code))

            for child in node.children:
                collect_imports(child)

        collect_imports(root_node)

        if imports:
            return CodeChunk(
                text='\n'.join(imports),
                type='file',
                language=language,
                file_path=file_path,
                start_line=0,
                end_line=len(imports) - 1,
                name='imports',
                metadata={
                    'import_count': len(imports),
                }
            )

        return None

    def split_file(self, code: str, file_path: Union[str, Path]) -> List[CodeChunk]:
        """
        Split a code file into structured chunks.

        Args:
            code: Source code as string
            file_path: Path to the file

        Returns:
            List of code chunks
        """
        file_path = str(file_path)
        language = self.detect_language(file_path)

        if not language:
            logger.warning(f"Unsupported language for file: {file_path}")
            return []

        # Parse code
        tree = self.parse_code(code, language)
        if not tree:
            logger.error(f"Failed to parse {file_path}")
            return []

        chunks = []

        # Extract imports as file-level chunk
        imports_chunk = self.extract_imports(tree, code, language, file_path)
        if imports_chunk:
            chunks.append(imports_chunk)

        # Extract classes
        class_chunks = self.extract_class_chunks(tree, code, language, file_path)
        chunks.extend(class_chunks)

        # Extract functions and methods
        function_chunks = self.extract_function_chunks(tree, code, language, file_path)
        chunks.extend(function_chunks)

        logger.info(f"Extracted {len(chunks)} chunks from {file_path} ({language})")
        return chunks

    def split_text(self, text: str, file_path: str) -> List[str]:
        """
        Split text into chunks (compatibility method).

        Args:
            text: Source code
            file_path: File path for language detection

        Returns:
            List of chunk texts
        """
        chunks = self.split_file(text, file_path)
        return [chunk.text for chunk in chunks]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split LangChain documents into smaller code chunks.

        Args:
            documents: List of Document objects containing code

        Returns:
            List of Document chunks
        """
        chunked_docs = []

        for doc in documents:
            # Handle both LangChain and other document formats
            file_path = doc.metadata.get('file_path', 'unknown.py')
            
            # Extract content from document
            if hasattr(doc, 'page_content'):
                content = doc.page_content
            elif hasattr(doc, 'text'):
                content = doc.text
            else:
                content = str(doc)
            
            chunks = self.split_file(content, file_path)

            for i, chunk in enumerate(chunks):
                # Create new Document for each chunk
                chunk_doc = Document(
                    page_content=chunk.text,
                    metadata={
                        **doc.metadata,
                        'chunk_type': chunk.type,
                        'chunk_name': chunk.name,
                        'chunk_signature': chunk.signature,
                        'chunk_docstring': chunk.docstring,
                        'parent_class': chunk.parent_class,
                        'start_line': chunk.start_line,
                        'end_line': chunk.end_line,
                        'language': chunk.language,
                        'chunk_metadata': chunk.metadata,
                        'id': f"{file_path}_{chunk.type}_{chunk.name}_{i}"
                    }
                )
                chunked_docs.append(chunk_doc)

            logger.info(f"Split {file_path} into {len(chunks)} code chunks")

        return chunked_docs


def create_ast_splitter() -> ASTCodeSplitter:
    """
    Factory function to create AST code splitter with environment variable defaults.

    Returns:
        ASTCodeSplitter instance
    """
    # Get values from environment variables or use defaults
    min_tokens = int(os.environ.get("CODE_CHUNKING_MIN_TOKENS", "100"))
    max_tokens = int(os.environ.get("CODE_CHUNKING_MAX_TOKENS", "2000"))

    logger.info(f"Creating AST splitter with min_tokens={min_tokens}, max_tokens={max_tokens}")

    return ASTCodeSplitter(
        min_tokens=min_tokens,
        max_tokens=max_tokens
    )
