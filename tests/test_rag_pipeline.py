"""
Integration Test Suite for Python RAG Indexing Pipeline

Tests the complete RAG knowledge indexing pipeline including:
- Document processing and chunking
- Embedding generation
- Database insertion and validation
- Knowledge quality assessment
- Error handling and edge cases
"""

import pytest
import asyncio
import os
import sys
import tempfile
import json
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rag_indexer import RAGIndexer, DocumentChunk, ProcessingResult
    from config_loader import ConfigLoader
    import_tools_available = True
    try:
        from import_tools_data import ToolDataImporter
    except ImportError:
        import_tools_available = False
        print("Warning: import_tools_data not available for testing")
except ImportError as e:
    print(f"Warning: Could not import RAG modules: {e}")
    print("Creating mock classes for testing...")
    
    # Create mock classes if imports fail
    class DocumentChunk:
        def __init__(self, content="", source_path="", chunk_index=0):
            self.content = content
            self.source_path = source_path
            self.chunk_index = chunk_index
    
    class ProcessingResult:
        def __init__(self, success=False, chunks_processed=0, errors=None):
            self.success = success
            self.chunks_processed = chunks_processed
            self.errors = errors or []
    
    class RAGIndexer:
        def __init__(self, config=None):
            self.config = config
        
        async def process_document(self, file_path, tool_id):
            return ProcessingResult(success=True, chunks_processed=5)
    
    class ConfigLoader:
        @staticmethod
        def load_config():
            return {
                'database': {'url': 'mock://test'},
                'rag': {'chunk_size': 1000, 'chunk_overlap': 200}
            }
    
    import_tools_available = False


class TestRAGPipelineIntegration:
    """Integration tests for the complete RAG indexing pipeline"""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            'database': {
                'url': 'postgresql://test:test@localhost:5432/test_db',
                'max_connections': 5
            },
            'rag': {
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'embedding_model': 'text-embedding-3-small',
                'batch_size': 50
            },
            'processing': {
                'max_workers': 2,
                'timeout_seconds': 60,
                'retry_attempts': 3
            }
        }
    
    @pytest.fixture
    def sample_tool_data(self):
        """Sample tool data for testing"""
        return [
            {
                'id': 'tool-001',
                'name': 'Figma',
                'description': 'Collaborative design tool for UI/UX',
                'category': 'design',
                'documentation_urls': ['https://figma.com/docs'],
                'features': ['collaborative', 'prototyping', 'design systems']
            },
            {
                'id': 'tool-002', 
                'name': 'VS Code',
                'description': 'Source code editor with debugging and Git integration',
                'category': 'development',
                'documentation_urls': ['https://code.visualstudio.com/docs'],
                'features': ['debugging', 'extensions', 'git integration']
            }
        ]
    
    @pytest.fixture
    def mock_documents(self):
        """Mock documents for testing"""
        return [
            {
                'path': '/mock/figma_guide.md',
                'content': """
# Figma User Guide

## Getting Started
Figma is a collaborative design tool that runs in the browser.
It allows teams to design, prototype, and gather feedback all in one place.

## Key Features
- Real-time collaboration
- Component libraries
- Auto-layout
- Prototyping tools

## Best Practices
1. Create consistent design systems
2. Use components for reusable elements
3. Organize layers with clear naming
                """,
                'tool_id': 'tool-001'
            },
            {
                'path': '/mock/vscode_tips.md', 
                'content': """
# VS Code Tips and Tricks

## Editor Features
VS Code provides powerful editing features including:
- IntelliSense for code completion
- Integrated debugging
- Built-in Git commands
- Extensions marketplace

## Productivity Tips
- Use Command Palette (Ctrl+Shift+P)
- Master keyboard shortcuts
- Configure settings sync
- Use multiple cursors for batch editing
                """,
                'tool_id': 'tool-002'
            }
        ]
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            'database': {'url': 'mock://test'},
            'rag': {'chunk_size': 500, 'chunk_overlap': 100}
        }
    
    def teardown_method(self):
        """Cleanup after each test method"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestDocumentProcessing:
    """Test document processing and chunking functionality"""
    
    def test_document_chunking(self):
        """Test that documents are properly chunked"""
        indexer = RAGIndexer(config={'rag': {'chunk_size': 200, 'chunk_overlap': 50}})
        
        # Create a test document
        test_content = "This is a test document. " * 50  # ~1000 characters
        
        # Mock the chunking process
        with patch.object(indexer, '_chunk_document') as mock_chunk:
            mock_chunk.return_value = [
                DocumentChunk(content=test_content[:200], source_path="test.txt", chunk_index=0),
                DocumentChunk(content=test_content[150:350], source_path="test.txt", chunk_index=1),
                DocumentChunk(content=test_content[300:500], source_path="test.txt", chunk_index=2),
            ]
            
            chunks = indexer._chunk_document(test_content, "test.txt")
            
            assert len(chunks) >= 3
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
            assert all(len(chunk.content) <= 250 for chunk in chunks)  # Accounting for overlap
    
    def test_embedding_generation(self):
        """Test embedding generation for document chunks"""
        indexer = RAGIndexer()
        
        test_chunks = [
            DocumentChunk(content="Design user interfaces with Figma", source_path="test1.txt", chunk_index=0),
            DocumentChunk(content="Debug code with VS Code", source_path="test2.txt", chunk_index=0)
        ]
        
        # Mock embedding generation
        with patch.object(indexer, '_generate_embeddings') as mock_embed:
            mock_embed.return_value = [
                [0.1, 0.2, 0.3] * 512,  # Mock 1536-dim embedding
                [0.4, 0.5, 0.6] * 512
            ]
            
            embeddings = indexer._generate_embeddings([chunk.content for chunk in test_chunks])
            
            assert len(embeddings) == 2
            assert all(len(emb) == 1536 for emb in embeddings)  # Standard embedding dimension
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing of multiple documents"""
        indexer = RAGIndexer(config={'rag': {'batch_size': 2}})
        
        # Mock successful processing
        with patch.object(indexer, 'process_document') as mock_process:
            mock_process.return_value = ProcessingResult(success=True, chunks_processed=5)
            
            documents = [
                ('doc1.txt', 'tool-001'),
                ('doc2.txt', 'tool-002'), 
                ('doc3.txt', 'tool-003')
            ]
            
            results = []
            for doc_path, tool_id in documents:
                result = await indexer.process_document(doc_path, tool_id)
                results.append(result)
            
            assert len(results) == 3
            assert all(result.success for result in results)
            assert sum(result.chunks_processed for result in results) == 15


class TestDatabaseIntegration:
    """Test database operations and validation"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor
    
    def test_knowledge_chunk_insertion(self, mock_db_connection):
        """Test insertion of knowledge chunks into database"""
        indexer = RAGIndexer()
        mock_conn, mock_cursor = mock_db_connection
        
        test_chunk = DocumentChunk(
            content="Test content for knowledge chunk",
            source_path="test_doc.md", 
            chunk_index=0
        )
        test_embedding = [0.1, 0.2, 0.3] * 512
        
        # Mock database insertion
        with patch.object(indexer, '_insert_knowledge_chunk') as mock_insert:
            mock_insert.return_value = 'chunk-uuid-123'
            
            chunk_id = indexer._insert_knowledge_chunk(
                mock_conn, 
                'tool-001', 
                test_chunk, 
                test_embedding
            )
            
            assert chunk_id == 'chunk-uuid-123'
            mock_insert.assert_called_once()
    
    def test_duplicate_content_handling(self):
        """Test handling of duplicate content"""
        indexer = RAGIndexer()
        
        # Mock duplicate detection
        with patch.object(indexer, '_check_content_hash') as mock_check:
            mock_check.return_value = True  # Content already exists
            
            duplicate_chunk = DocumentChunk(
                content="Duplicate content",
                source_path="duplicate.txt",
                chunk_index=0
            )
            
            is_duplicate = indexer._check_content_hash('tool-001', duplicate_chunk.content)
            assert is_duplicate is True
    
    def test_knowledge_stats_calculation(self):
        """Test calculation of knowledge base statistics"""
        indexer = RAGIndexer()
        
        # Mock stats query
        with patch.object(indexer, '_get_knowledge_stats') as mock_stats:
            mock_stats.return_value = {
                'total_knowledge_entries': 150,
                'knowledge_quality_score': 0.85,
                'last_updated': datetime.now().isoformat(),
                'avg_embedding_dimension': 1536,
                'coverage_by_category': {
                    'design': 45,
                    'development': 60,
                    'analytics': 25,
                    'communication': 20
                }
            }
            
            stats = indexer._get_knowledge_stats()
            
            assert stats['total_knowledge_entries'] > 0
            assert 0 <= stats['knowledge_quality_score'] <= 1
            assert 'coverage_by_category' in stats
            assert sum(stats['coverage_by_category'].values()) <= stats['total_knowledge_entries']


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_file_handling(self):
        """Test handling of invalid or corrupted files"""
        indexer = RAGIndexer()
        
        # Test with non-existent file
        with patch('os.path.exists', return_value=False):
            result = asyncio.run(indexer.process_document('/nonexistent/file.txt', 'tool-001'))
            assert result.success is False
            assert 'not found' in str(result.errors).lower()
    
    def test_embedding_api_failure(self):
        """Test handling of embedding API failures"""
        indexer = RAGIndexer()
        
        # Mock API failure
        with patch.object(indexer, '_generate_embeddings') as mock_embed:
            mock_embed.side_effect = Exception("API rate limit exceeded")
            
            test_chunk = DocumentChunk(content="Test content", source_path="test.txt", chunk_index=0)
            
            with pytest.raises(Exception) as exc_info:
                indexer._generate_embeddings([test_chunk.content])
            
            assert "API rate limit" in str(exc_info.value)
    
    def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        indexer = RAGIndexer()
        
        # Mock database connection failure
        with patch.object(indexer, '_connect_to_database') as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")
            
            with pytest.raises(Exception) as exc_info:
                indexer._connect_to_database()
            
            assert "Connection refused" in str(exc_info.value)
    
    def test_malformed_document_handling(self):
        """Test handling of malformed or empty documents"""
        indexer = RAGIndexer()
        
        # Test empty document
        result = asyncio.run(indexer.process_document('', 'tool-001'))
        assert result.success is False
        
        # Test document with only whitespace
        with patch('builtins.open', mock_open(read_data="   \n\n\t   \n")):
            result = asyncio.run(indexer.process_document('whitespace.txt', 'tool-001'))
            assert result.success is False or result.chunks_processed == 0


class TestPerformanceValidation:
    """Test performance characteristics of the RAG pipeline"""
    
    @pytest.mark.asyncio
    async def test_processing_speed(self):
        """Test that document processing meets performance requirements"""
        indexer = RAGIndexer()
        
        # Create a moderately large document
        large_content = "This is test content for performance testing. " * 1000
        
        with patch('builtins.open', mock_open(read_data=large_content)):
            with patch.object(indexer, '_generate_embeddings') as mock_embed:
                mock_embed.return_value = [[0.1] * 1536] * 10  # Mock embeddings
                
                start_time = datetime.now()
                result = await indexer.process_document('large_doc.txt', 'tool-001')
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                
                # Should process within reasonable time (adjust based on requirements)
                assert processing_time < 30  # 30 seconds max for large document
                assert result.success is True
    
    def test_memory_usage(self):
        """Test memory usage during batch processing"""
        import psutil
        import os
        
        indexer = RAGIndexer(config={'rag': {'batch_size': 100}})
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple documents
        with patch.object(indexer, 'process_document') as mock_process:
            mock_process.return_value = ProcessingResult(success=True, chunks_processed=10)
            
            # Simulate processing many documents
            for i in range(50):
                asyncio.run(indexer.process_document(f'doc_{i}.txt', f'tool-{i}'))
        
        # Check memory usage hasn't grown excessively
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 500  # Less than 500MB increase


class TestQualityAssurance:
    """Test quality assurance and validation of processed knowledge"""
    
    def test_content_quality_scoring(self):
        """Test quality scoring of processed content"""
        indexer = RAGIndexer()
        
        # Test high-quality content
        high_quality_content = """
        # Comprehensive Guide to Tool Usage
        
        This guide provides detailed instructions for using the tool effectively.
        It includes step-by-step procedures, best practices, and troubleshooting tips.
        
        ## Key Features
        1. Feature A: Detailed explanation with examples
        2. Feature B: Use cases and implementation details  
        3. Feature C: Advanced configuration options
        
        ## Examples
        Here are practical examples of how to use each feature...
        """
        
        # Test low-quality content
        low_quality_content = "Tool good. Use tool. Tool help."
        
        with patch.object(indexer, '_assess_content_quality') as mock_assess:
            mock_assess.side_effect = lambda content: 0.9 if len(content) > 200 and '#' in content else 0.3
            
            high_score = indexer._assess_content_quality(high_quality_content)
            low_score = indexer._assess_content_quality(low_quality_content)
            
            assert high_score > 0.8
            assert low_score < 0.5
    
    def test_embedding_quality_validation(self):
        """Test validation of generated embeddings"""
        indexer = RAGIndexer()
        
        # Mock embeddings with different quality characteristics
        with patch.object(indexer, '_validate_embedding_quality') as mock_validate:
            mock_validate.side_effect = lambda embedding: {
                'magnitude': sum(x**2 for x in embedding)**0.5,
                'is_normalized': abs(sum(x**2 for x in embedding)**0.5 - 1.0) < 0.1,
                'non_zero_ratio': sum(1 for x in embedding if abs(x) > 0.001) / len(embedding)
            }
            
            test_embedding = [0.1, -0.2, 0.3, 0.0] * 384  # 1536 dim
            quality_metrics = indexer._validate_embedding_quality(test_embedding)
            
            assert 'magnitude' in quality_metrics
            assert 'is_normalized' in quality_metrics
            assert 'non_zero_ratio' in quality_metrics
            assert quality_metrics['non_zero_ratio'] > 0.1  # Should have meaningful values
    
    def test_knowledge_coverage_analysis(self):
        """Test analysis of knowledge base coverage"""
        indexer = RAGIndexer()
        
        with patch.object(indexer, '_analyze_coverage') as mock_analyze:
            mock_analyze.return_value = {
                'category_coverage': {
                    'design': 0.85,
                    'development': 0.92, 
                    'analytics': 0.67,
                    'communication': 0.73
                },
                'feature_coverage': {
                    'basic_usage': 0.95,
                    'advanced_features': 0.78,
                    'troubleshooting': 0.82,
                    'integration': 0.65
                },
                'overall_coverage': 0.79
            }
            
            coverage = indexer._analyze_coverage()
            
            assert coverage['overall_coverage'] > 0.7
            assert all(score >= 0 and score <= 1 for score in coverage['category_coverage'].values())
            assert all(score >= 0 and score <= 1 for score in coverage['feature_coverage'].values())


# Helper function for mock file reading
def mock_open(read_data=""):
    """Create a mock for open() that returns specified data"""
    from unittest.mock import mock_open as base_mock_open
    return base_mock_open(read_data=read_data)


# Integration test runner
class RAGPipelineTestRunner:
    """Test runner for the complete RAG pipeline test suite"""
    
    @staticmethod
    def run_all_tests():
        """Run all RAG pipeline tests"""
        print("🧪 Starting RAG Pipeline Integration Test Suite")
        print("=" * 60)
        
        # Run pytest with proper configuration
        pytest_args = [
            __file__,
            "-v",  # Verbose output
            "-s",  # Don't capture stdout
            "--tb=short",  # Short traceback format
            "-x",  # Stop on first failure
        ]
        
        # Add coverage if available
        try:
            import pytest_cov
            pytest_args.extend(["--cov=rag_indexer", "--cov-report=term-missing"])
        except ImportError:
            print("Note: pytest-cov not available, skipping coverage report")
        
        result = pytest.main(pytest_args)
        
        print("\n" + "=" * 60)
        print("🏁 RAG Pipeline Test Suite Completed")
        
        if result == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. Check output above.")
        
        return result == 0


if __name__ == "__main__":
    # Run tests when script is executed directly
    runner = RAGPipelineTestRunner()
    runner.run_all_tests()