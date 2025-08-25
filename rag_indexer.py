#!/usr/bin/env python3
"""
RAG Indexing Pipeline for FlowGenius Knowledge Management
Integrates with RAG-Anything for document processing and embedding generation
"""

import os
import sys
import json
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse
import time

# Core dependencies
import pandas as pd
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv

# Document processing
try:
    from raganything import RAGAnything
    from raganything.loaders import PDFLoader, URLLoader, TextLoader
    from raganything.splitters import RecursiveCharacterTextSplitter
    from raganything.document import Document
except ImportError:
    print("Warning: raganything not installed. Install with: pip install raganything[all]")
    RAGAnything = None

# Alternative document processing
import PyPDF2
import pdfplumber
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import tiktoken

# Configuration and validation
from pydantic import BaseModel, Field, validator
import yaml
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    Path(__file__).parent / "logs" / "rag_indexer.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="1 week"
)

# Create logs directory if it doesn't exist
(Path(__file__).parent / "logs").mkdir(exist_ok=True)

@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    processing_version: str = "1.0"
    embedding_model: str = "text-embedding-004"
    batch_size: int = 10
    rate_limit_delay: float = 0.1
    max_retries: int = 3

@dataclass
class SourceMetadata:
    """Metadata for document sources"""
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    page_count: Optional[int] = None
    url_status: Optional[int] = None
    encoding: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

class DocumentChunk:
    """Represents a processed document chunk"""
    
    def __init__(
        self,
        content: str,
        chunk_index: int,
        source_path: str,
        source_type: str,
        source_title: str = "",
        metadata: Optional[SourceMetadata] = None
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.source_path = source_path
        self.source_type = source_type
        self.source_title = source_title or self._extract_title_from_path(source_path)
        self.metadata = metadata or SourceMetadata()
        self.content_hash = self._generate_hash()
        self.chunk_size = len(content)
        self.embedding: Optional[List[float]] = None
        self.relevance_score: Optional[float] = None
        self.quality_score: Optional[float] = None

    def _extract_title_from_path(self, path: str) -> str:
        """Extract title from file path or URL"""
        if path.startswith(('http://', 'https://')):
            return urlparse(path).path.split('/')[-1] or path
        return Path(path).stem

    def _generate_hash(self) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(self.content.encode('utf-8')).hexdigest()

class RAGProcessor:
    """Main class for RAG document processing and indexing"""
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.supabase = self._init_supabase()
        self.embedding_model = self._init_embedding_model()
        self.rag_anything = self._init_rag_anything()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        ) if RAGAnything else None
        
        # Token encoder for text processing
        try:
            self.token_encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.token_encoder = tiktoken.get_encoding("cl100k_base")

    def _init_supabase(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            raise ValueError("Missing Supabase configuration. Check environment variables.")
        
        return create_client(url, key)

    def _init_embedding_model(self):
        """Initialize Google AI embedding model"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing Google AI API key. Check GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        return self.config.embedding_model  # Return model name for embed_content function

    def _init_rag_anything(self):
        """Initialize RAG-Anything if available"""
        if RAGAnything is None:
            logger.warning("RAG-Anything not available. Using fallback document processing.")
            return None
        
        try:
            return RAGAnything()
        except Exception as e:
            logger.warning(f"Failed to initialize RAG-Anything: {e}. Using fallback processing.")
            return None

    async def process_document(
        self, 
        source_path: str, 
        source_type: str,
        tool_id: str,
        custom_title: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Process a document and return chunks"""
        logger.info(f"Processing document: {source_path} (type: {source_type})")
        
        try:
            # Load and process document
            if self.rag_anything and source_type in ['pdf', 'url']:
                chunks = await self._process_with_rag_anything(source_path, source_type, custom_title)
            else:
                chunks = await self._process_with_fallback(source_path, source_type, custom_title)
            
            logger.info(f"Generated {len(chunks)} chunks from {source_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process document {source_path}: {e}")
            raise

    async def _process_with_rag_anything(
        self, 
        source_path: str, 
        source_type: str,
        custom_title: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Process document using RAG-Anything"""
        chunks = []
        
        try:
            # Load document
            if source_type == 'pdf':
                loader = PDFLoader(source_path)
            elif source_type == 'url':
                loader = URLLoader(source_path)
            elif source_type == 'text':
                loader = TextLoader(source_path)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            documents = loader.load()
            
            # Split documents into chunks
            for doc_idx, document in enumerate(documents):
                if self.text_splitter:
                    text_chunks = self.text_splitter.split_text(document.page_content)
                else:
                    # Fallback chunking
                    text_chunks = self._simple_chunk_text(document.page_content)
                
                for i, chunk_text in enumerate(text_chunks):
                    if len(chunk_text.strip()) < self.config.min_chunk_size:
                        continue
                    
                    # Extract metadata
                    metadata = SourceMetadata()
                    if hasattr(document, 'metadata') and document.metadata:
                        metadata.additional_info = document.metadata
                    
                    chunk = DocumentChunk(
                        content=chunk_text.strip(),
                        chunk_index=len(chunks),
                        source_path=source_path,
                        source_type=source_type,
                        source_title=custom_title or document.metadata.get('title', ''),
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    
        except Exception as e:
            logger.error(f"RAG-Anything processing failed: {e}")
            # Fallback to manual processing
            chunks = await self._process_with_fallback(source_path, source_type, custom_title)
        
        return chunks

    async def _process_with_fallback(
        self, 
        source_path: str, 
        source_type: str,
        custom_title: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Fallback document processing without RAG-Anything"""
        chunks = []
        
        try:
            # Extract text based on source type
            if source_type == 'pdf':
                text_content = self._extract_pdf_text(source_path)
            elif source_type == 'url':
                text_content = self._extract_url_text(source_path)
            elif source_type == 'text' or source_type == 'markdown':
                text_content = self._extract_text_file(source_path)
            else:
                raise ValueError(f"Unsupported source type for fallback processing: {source_type}")
            
            # Chunk the text
            text_chunks = self._simple_chunk_text(text_content)
            
            for i, chunk_text in enumerate(text_chunks):
                if len(chunk_text.strip()) < self.config.min_chunk_size:
                    continue
                
                chunk = DocumentChunk(
                    content=chunk_text.strip(),
                    chunk_index=i,
                    source_path=source_path,
                    source_type=source_type,
                    source_title=custom_title,
                    metadata=SourceMetadata()
                )
                
                chunks.append(chunk)
                
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            raise
        
        return chunks

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text_parts = []
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    if page.extract_text():
                        text_parts.append(page.extract_text())
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}. Trying pypdf2...")
            
            # Fallback to pypdf2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = pypdf2.PdfReader(file)
                    for page in pdf_reader.pages:
                        if page.extract_text():
                            text_parts.append(page.extract_text())
            except Exception as e2:
                logger.error(f"Both PDF extraction methods failed: {e2}")
                raise
        
        return '\n\n'.join(text_parts)

    def _extract_url_text(self, url: str) -> str:
        """Extract text from web URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from URL {url}: {e}")
            raise

    def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text or markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except:
                    continue
            raise ValueError(f"Could not decode text file: {file_path}")

    def _simple_chunk_text(self, text: str) -> List[str]:
        """Simple text chunking based on token count"""
        if not text.strip():
            return []
        
        # Split into sentences first
        sentences = text.replace('\n\n', ' [PARAGRAPH] ').split('. ')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_tokens = len(self.token_encoder.encode(sentence))
            
            # If adding this sentence would exceed chunk size, start new chunk
            if current_length + sentence_tokens > self.config.chunk_size and current_chunk:
                chunk_text = '. '.join(current_chunk).replace(' [PARAGRAPH] ', '\n\n')
                if len(chunk_text.strip()) >= self.config.min_chunk_size:
                    chunks.append(chunk_text.strip())
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(self.token_encoder.encode(s)) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk).replace(' [PARAGRAPH] ', '\n\n')
            if len(chunk_text.strip()) >= self.config.min_chunk_size:
                chunks.append(chunk_text.strip())
        
        return chunks

    async def generate_embeddings(self, chunks: List[DocumentChunk]) -> None:
        """Generate embeddings for document chunks"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        for i, chunk in enumerate(tqdm(chunks, desc="Generating embeddings")):
            try:
                # Generate embedding
                embedding_result = genai.embed_content(model=self.embedding_model, content=chunk.content)
                chunk.embedding = embedding_result['embedding']
                
                # Simple quality scoring based on content length and structure
                chunk.quality_score = self._calculate_quality_score(chunk.content)
                
                # Rate limiting
                if i < len(chunks) - 1:
                    await asyncio.sleep(self.config.rate_limit_delay)
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                chunk.embedding = None

    def _calculate_quality_score(self, content: str) -> float:
        """Calculate a simple quality score for content"""
        score = 0.5  # Base score
        
        # Length score
        if 200 <= len(content) <= 1500:
            score += 0.2
        elif len(content) > 1500:
            score += 0.1
        
        # Structure indicators
        if any(indicator in content.lower() for indicator in ['however', 'therefore', 'because', 'furthermore']):
            score += 0.1
        
        # Technical content indicators
        if any(indicator in content.lower() for indicator in ['api', 'feature', 'integration', 'performance']):
            score += 0.1
        
        # Sentence structure
        sentences = content.count('.')
        if 3 <= sentences <= 10:
            score += 0.1
        
        return min(score, 1.0)

    async def store_chunks(self, chunks: List[DocumentChunk], tool_id: str) -> Dict[str, Any]:
        """Store processed chunks in the database"""
        logger.info(f"Storing {len(chunks)} chunks for tool {tool_id}")
        
        stored_count = 0
        skipped_count = 0
        failed_count = 0
        
        for chunk in tqdm(chunks, desc="Storing chunks"):
            try:
                # Check for existing chunk with same hash
                existing = self.supabase.table("rag_knowledge_chunks").select("id").eq(
                    "tool_id", tool_id
                ).eq("content_hash", chunk.content_hash).execute()
                
                if existing.data:
                    logger.debug(f"Skipping duplicate chunk: {chunk.content_hash}")
                    skipped_count += 1
                    continue
                
                # Prepare data for storage
                chunk_data = {
                    "tool_id": tool_id,
                    "source_type": chunk.source_type,
                    "source_path": chunk.source_path,
                    "source_title": chunk.source_title,
                    "source_metadata": chunk.metadata.__dict__ if chunk.metadata else {},
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    # "chunk_size": chunk.chunk_size,  # Removed due to schema cache issue
                    "embedding": chunk.embedding,
                    "processing_version": self.config.processing_version,
                    "relevance_score": chunk.relevance_score,
                    "quality_score": chunk.quality_score,
                    "is_active": True
                }
                
                # Store in database
                result = self.supabase.table("rag_knowledge_chunks").insert(chunk_data).execute()
                
                if result.data:
                    stored_count += 1
                else:
                    logger.warning(f"Failed to store chunk: {chunk.content_hash}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing chunk {chunk.content_hash}: {e}")
                failed_count += 1
        
        summary = {
            "total_chunks": len(chunks),
            "stored": stored_count,
            "skipped": skipped_count,
            "failed": failed_count
        }
        
        logger.info(f"Storage summary: {summary}")
        return summary

    async def index_document(
        self, 
        source_path: str, 
        tool_id: str,
        source_type: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete pipeline to index a document"""
        
        # Auto-detect source type if not provided
        if source_type is None:
            source_type = self._detect_source_type(source_path)
        
        logger.info(f"Starting document indexing pipeline for {source_path}")
        logger.info(f"Tool ID: {tool_id}, Source type: {source_type}")
        
        try:
            # Verify tool exists
            tool_result = self.supabase.table("tools").select("id,name").eq("id", tool_id).execute()
            if not tool_result.data:
                raise ValueError(f"Tool with ID {tool_id} not found")
            
            tool_name = tool_result.data[0]['name']
            logger.info(f"Processing knowledge for tool: {tool_name}")
            
            # Process document
            chunks = await self.process_document(source_path, source_type, tool_id, custom_title)
            
            if not chunks:
                raise ValueError("No chunks generated from document")
            
            # Generate embeddings
            await self.generate_embeddings(chunks)
            
            # Filter chunks with valid embeddings
            valid_chunks = [chunk for chunk in chunks if chunk.embedding is not None]
            logger.info(f"Generated embeddings for {len(valid_chunks)}/{len(chunks)} chunks")
            
            if not valid_chunks:
                raise ValueError("No valid embeddings generated")
            
            # Store chunks
            storage_summary = await self.store_chunks(valid_chunks, tool_id)
            
            # Final summary
            result = {
                "success": True,
                "tool_id": tool_id,
                "tool_name": tool_name,
                "source_path": source_path,
                "source_type": source_type,
                "processing_summary": {
                    "total_chunks_processed": len(chunks),
                    "chunks_with_embeddings": len(valid_chunks),
                    **storage_summary
                }
            }
            
            logger.info(f"Document indexing completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id,
                "source_path": source_path
            }

    def _detect_source_type(self, source_path: str) -> str:
        """Auto-detect source type from path/URL"""
        if source_path.startswith(('http://', 'https://')):
            return 'url'
        
        path = Path(source_path)
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return 'pdf'
        elif suffix in ['.txt', '.md', '.markdown']:
            return 'text' if suffix == '.txt' else 'markdown'
        elif suffix in ['.doc', '.docx']:
            return 'document'
        else:
            return 'text'  # Default fallback

    async def get_tool_knowledge_stats(self, tool_id: str) -> Dict[str, Any]:
        """Get knowledge statistics for a specific tool"""
        try:
            # Get summary using database function
            result = self.supabase.rpc(
                'get_tool_knowledge_summary',
                {'input_tool_id': tool_id, 'max_chunks': 10}
            ).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return {
                    "success": True,
                    "tool_id": tool_id,
                    "chunk_count": data.get('chunk_count', 0),
                    "sources": data.get('sources', []),
                    "top_chunks": data.get('top_chunks', [])
                }
            else:
                return {
                    "success": True,
                    "tool_id": tool_id,
                    "chunk_count": 0,
                    "sources": [],
                    "top_chunks": []
                }
                
        except Exception as e:
            logger.error(f"Failed to get knowledge stats for tool {tool_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id
            }

    async def cleanup_tool_knowledge(self, tool_id: str, source_path: Optional[str] = None) -> Dict[str, Any]:
        """Clean up knowledge chunks for a tool (optionally filtered by source)"""
        try:
            query = self.supabase.table("rag_knowledge_chunks").delete().eq("tool_id", tool_id)
            
            if source_path:
                query = query.eq("source_path", source_path)
            
            result = query.execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            logger.info(f"Deleted {deleted_count} chunks for tool {tool_id}")
            
            return {
                "success": True,
                "tool_id": tool_id,
                "source_path": source_path,
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup knowledge for tool {tool_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id
            }