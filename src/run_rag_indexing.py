#!/usr/bin/env python3
"""
CLI Interface for RAG Knowledge Indexing
Provides manual knowledge management capabilities for FlowGenius tools
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional
import json

from rag_indexer import RAGProcessor, ProcessingConfig
from loguru import logger
import pandas as pd

def setup_cli_logging(verbose: bool = False):
    """Setup logging for CLI usage"""
    logger.remove()  # Remove default handlers
    
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level
    )

async def index_document_command(args):
    """Command to index a single document"""
    logger.info(f"🚀 Starting document indexing...")
    logger.info(f"📄 Source: {args.source_path}")
    logger.info(f"🔧 Tool ID: {args.tool_id}")
    
    # Initialize processor
    config = ProcessingConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size
    )
    processor = RAGProcessor(config)
    
    # Run indexing
    result = await processor.index_document(
        source_path=args.source_path,
        tool_id=args.tool_id,
        source_type=args.source_type,
        custom_title=args.title
    )
    
    if result['success']:
        logger.info("✅ Document indexing completed successfully!")
        logger.info(f"📊 Processing Summary:")
        summary = result['processing_summary']
        logger.info(f"   • Total chunks: {summary['total_chunks_processed']}")
        logger.info(f"   • With embeddings: {summary['chunks_with_embeddings']}")
        logger.info(f"   • Stored: {summary['stored']}")
        logger.info(f"   • Skipped (duplicates): {summary['skipped']}")
        if summary['failed'] > 0:
            logger.warning(f"   • Failed: {summary['failed']}")
    else:
        logger.error(f"❌ Document indexing failed: {result['error']}")
        sys.exit(1)

async def list_tools_command(args):
    """Command to list available tools"""
    processor = RAGProcessor()
    
    try:
        result = processor.supabase.table("tools").select("id,name,description,categories").eq("is_active", True).order("name").execute()
        
        if result.data:
            logger.info(f"📋 Available Tools ({len(result.data)} total):")
            
            for tool in result.data:
                categories = ', '.join(tool.get('categories', []))
                description = tool.get('description', 'No description')[:80] + ('...' if len(tool.get('description', '')) > 80 else '')
                
                logger.info(f"")
                logger.info(f"   🔧 {tool['name']}")
                logger.info(f"      ID: {tool['id']}")
                logger.info(f"      Categories: {categories}")
                logger.info(f"      Description: {description}")
        else:
            logger.warning("No tools found in database")
            
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        sys.exit(1)

async def tool_stats_command(args):
    """Command to show knowledge statistics for a tool"""
    processor = RAGProcessor()
    
    result = await processor.get_tool_knowledge_stats(args.tool_id)
    
    if result['success']:
        logger.info(f"📊 Knowledge Statistics for Tool: {args.tool_id}")
        logger.info(f"   • Total chunks: {result['chunk_count']}")
        
        if result['sources']:
            logger.info(f"   • Sources:")
            for source in result['sources']:
                logger.info(f"     - {source['source_title']} ({source['source_type']}) - {source['chunk_count']} chunks")
        
        if result['top_chunks']:
            logger.info(f"   • Top content samples:")
            for i, chunk in enumerate(result['top_chunks'][:3], 1):
                score = chunk.get('relevance_score', 'N/A')
                content_preview = chunk['content'][:100] + '...' if len(chunk['content']) > 100 else chunk['content']
                logger.info(f"     {i}. [{score}] {content_preview}")
    else:
        logger.error(f"Failed to get tool stats: {result['error']}")

async def cleanup_command(args):
    """Command to clean up knowledge for a tool"""
    processor = RAGProcessor()
    
    if not args.confirm:
        logger.warning("⚠️  This will permanently delete knowledge chunks!")
        if args.source_path:
            logger.warning(f"   Filtering by source: {args.source_path}")
        else:
            logger.warning("   All chunks for this tool will be deleted!")
        logger.warning("   Add --confirm flag to proceed.")
        sys.exit(1)
    
    result = await processor.cleanup_tool_knowledge(
        tool_id=args.tool_id,
        source_path=args.source_path
    )
    
    if result['success']:
        logger.info(f"✅ Cleanup completed: {result['deleted_count']} chunks deleted")
    else:
        logger.error(f"❌ Cleanup failed: {result['error']}")
        sys.exit(1)

async def batch_index_command(args):
    """Command to batch index multiple documents"""
    if not Path(args.batch_file).exists():
        logger.error(f"Batch file not found: {args.batch_file}")
        sys.exit(1)
    
    # Read batch configuration
    try:
        if args.batch_file.endswith('.json'):
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)
        elif args.batch_file.endswith('.csv'):
            df = pd.read_csv(args.batch_file)
            batch_config = df.to_dict('records')
        else:
            logger.error("Batch file must be JSON or CSV format")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to read batch file: {e}")
        sys.exit(1)
    
    logger.info(f"🚀 Starting batch indexing of {len(batch_config)} items...")
    
    # Initialize processor
    config = ProcessingConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size
    )
    processor = RAGProcessor(config)
    
    success_count = 0
    failed_count = 0
    
    for i, item in enumerate(batch_config, 1):
        logger.info(f"\n📄 [{i}/{len(batch_config)}] Processing: {item.get('source_path', 'Unknown')}")
        
        try:
            result = await processor.index_document(
                source_path=item['source_path'],
                tool_id=item['tool_id'],
                source_type=item.get('source_type'),
                custom_title=item.get('title')
            )
            
            if result['success']:
                success_count += 1
                logger.info(f"   ✅ Success: {result['processing_summary']['stored']} chunks stored")
            else:
                failed_count += 1
                logger.error(f"   ❌ Failed: {result['error']}")
                
        except Exception as e:
            failed_count += 1
            logger.error(f"   ❌ Error: {e}")
    
    logger.info(f"\n📊 Batch processing completed!")
    logger.info(f"   ✅ Successful: {success_count}")
    logger.info(f"   ❌ Failed: {failed_count}")

def create_sample_batch_file():
    """Create a sample batch configuration file"""
    sample_config = [
        {
            "source_path": "./data_sources/perplexity/perplexity_review.pdf",
            "tool_id": "123e4567-e89b-12d3-a456-426614174000",
            "source_type": "pdf",
            "title": "Perplexity Deep Dive Review"
        },
        {
            "source_path": "https://example.com/midjourney-guide",
            "tool_id": "987fcdeb-51a2-43d1-9f8e-123456789abc",
            "source_type": "url",
            "title": "Midjourney User Guide"
        }
    ]
    
    sample_file = Path(__file__).parent / "sample_batch.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info(f"📝 Sample batch file created: {sample_file}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="RAG Knowledge Indexing CLI for FlowGenius",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Index a PDF document
  python run_rag_indexing.py index --tool-id "abc-123" --source-path "./docs/guide.pdf"
  
  # Index a web URL with custom title
  python run_rag_indexing.py index --tool-id "abc-123" --source-path "https://example.com/guide" --title "Custom Guide"
  
  # List all available tools
  python run_rag_indexing.py list-tools
  
  # Show knowledge stats for a tool
  python run_rag_indexing.py stats --tool-id "abc-123"
  
  # Batch index from configuration file
  python run_rag_indexing.py batch --batch-file "./batch_config.json"
  
  # Clean up knowledge for a tool
  python run_rag_indexing.py cleanup --tool-id "abc-123" --confirm
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index a single document')
    index_parser.add_argument('--tool-id', required=True, help='UUID of the tool this knowledge is for')
    index_parser.add_argument('--source-path', required=True, help='Path to document or URL')
    index_parser.add_argument('--source-type', choices=['pdf', 'url', 'text', 'markdown'], help='Source type (auto-detected if not specified)')
    index_parser.add_argument('--title', help='Custom title for the document')
    index_parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size in tokens (default: 1000)')
    index_parser.add_argument('--chunk-overlap', type=int, default=200, help='Chunk overlap in tokens (default: 200)')
    index_parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing (default: 10)')
    
    # List tools command
    list_parser = subparsers.add_parser('list-tools', help='List available tools')
    
    # Tool stats command
    stats_parser = subparsers.add_parser('stats', help='Show knowledge statistics for a tool')
    stats_parser.add_argument('--tool-id', required=True, help='UUID of the tool')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up knowledge chunks for a tool')
    cleanup_parser.add_argument('--tool-id', required=True, help='UUID of the tool')
    cleanup_parser.add_argument('--source-path', help='Optional: only delete chunks from this source')
    cleanup_parser.add_argument('--confirm', action='store_true', help='Confirm deletion (required)')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch index multiple documents')
    batch_parser.add_argument('--batch-file', required=True, help='Path to batch configuration file (JSON or CSV)')
    batch_parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size in tokens (default: 1000)')
    batch_parser.add_argument('--chunk-overlap', type=int, default=200, help='Chunk overlap in tokens (default: 200)')
    batch_parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing (default: 10)')
    
    # Sample command
    sample_parser = subparsers.add_parser('create-sample', help='Create a sample batch configuration file')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_cli_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run appropriate command
    try:
        if args.command == 'index':
            asyncio.run(index_document_command(args))
        elif args.command == 'list-tools':
            asyncio.run(list_tools_command(args))
        elif args.command == 'stats':
            asyncio.run(tool_stats_command(args))
        elif args.command == 'cleanup':
            asyncio.run(cleanup_command(args))
        elif args.command == 'batch':
            asyncio.run(batch_index_command(args))
        elif args.command == 'create-sample':
            create_sample_batch_file()
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.warning("🛑 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()