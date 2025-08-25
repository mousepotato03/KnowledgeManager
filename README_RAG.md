# RAG Knowledge Indexing Pipeline

A comprehensive RAG (Retrieval-Augmented Generation) indexing pipeline for FlowGenius that processes documents and creates knowledge chunks with embeddings for enhanced tool matching accuracy.

## Overview

This system implements the manual knowledge indexing workflow described in the RAG-Anything guide, providing tools to:

- Process documents (PDF, web pages, text files) into semantic chunks
- Generate embeddings using Google AI's text-embedding-004 model
- Store knowledge chunks in Supabase with vector similarity search
- Provide CLI tools for manual knowledge management
- Support batch processing for multiple documents

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Documents     │───▶│   RAG Processor   │───▶│  rag_knowledge_     │
│  • PDF files    │    │  • Text extraction│    │     chunks          │
│  • Web URLs     │    │  • Chunking       │    │  • Content + hash   │
│  • Text files   │    │  • Embeddings     │    │  • Vector embeddings│
└─────────────────┘    │  • Quality scoring│    │  • Metadata         │
                       └──────────────────┘    └─────────────────────┘
                               │
                       ┌──────────────────┐
                       │   CLI Interface   │
                       │  • Manual indexing│
                       │  • Batch processing│
                       │  • Stats & cleanup│
                       └──────────────────┘
```

## Features

### Document Processing
- **Multi-format support**: PDF, web URLs, text files, Markdown
- **RAG-Anything integration**: Advanced document parsing with fallback processing
- **Smart chunking**: Configurable chunk sizes with semantic overlap
- **Quality scoring**: Content quality assessment for ranking

### Embedding Generation
- **Google AI integration**: Uses text-embedding-004 model
- **Batch processing**: Efficient API usage with rate limiting
- **Vector storage**: Optimized for similarity search in Supabase

### Database Integration
- **Supabase native**: Full integration with existing FlowGenius infrastructure
- **Vector search**: Built-in similarity search functions
- **Deduplication**: Content hash-based duplicate prevention
- **Metadata tracking**: Source information and processing metadata

### CLI Management
- **Interactive commands**: Easy-to-use command-line interface
- **Batch operations**: Process multiple documents at once
- **Statistics**: Knowledge base analytics per tool
- **Cleanup tools**: Remove outdated or incorrect knowledge

## Installation

### Prerequisites
- Python 3.8+
- Supabase account with vector extension enabled
- Google AI API key

### Setup

1. **Install dependencies**:
```bash
# Windows
run_rag_indexing.bat

# Linux/macOS  
./run_rag_indexing.sh
```

2. **Configure environment variables** in `.env`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GOOGLE_API_KEY=your_google_ai_key
```

3. **Run database migration**:
```sql
-- Apply the migration in Supabase SQL editor
-- File: workflow-ai/supabase/migrations/20250824000001_add_rag_knowledge_chunks.sql
```

## Usage Guide

### Basic Commands

#### 1. List Available Tools
```bash
python run_rag_indexing.py list-tools
```
This shows all tools in your database with their IDs, which you'll need for indexing.

#### 2. Index a Single Document

**PDF Document:**
```bash
python run_rag_indexing.py index \
  --tool-id "123e4567-e89b-12d3-a456-426614174000" \
  --source-path "./docs/perplexity_review.pdf" \
  --title "Perplexity Deep Dive Review"
```

**Web URL:**
```bash
python run_rag_indexing.py index \
  --tool-id "123e4567-e89b-12d3-a456-426614174000" \
  --source-path "https://blog.example.com/ai-tool-comparison" \
  --source-type "url" \
  --title "AI Tool Comparison Blog Post"
```

**Text File:**
```bash
python run_rag_indexing.py index \
  --tool-id "123e4567-e89b-12d3-a456-426614174000" \
  --source-path "./data/tool_analysis.md" \
  --source-type "markdown"
```

#### 3. View Knowledge Statistics
```bash
python run_rag_indexing.py stats --tool-id "123e4567-e89b-12d3-a456-426614174000"
```

#### 4. Batch Processing
```bash
# Create sample batch file
python run_rag_indexing.py create-sample

# Run batch processing
python run_rag_indexing.py batch --batch-file "batch_config.json"
```

#### 5. Cleanup Knowledge
```bash
# Remove all knowledge for a tool
python run_rag_indexing.py cleanup \
  --tool-id "123e4567-e89b-12d3-a456-426614174000" \
  --confirm

# Remove knowledge from specific source
python run_rag_indexing.py cleanup \
  --tool-id "123e4567-e89b-12d3-a456-426614174000" \
  --source-path "./docs/old_guide.pdf" \
  --confirm
```

### Advanced Configuration

#### Configuration File (`config.yaml`)
```yaml
processing:
  chunk_size: 1000          # Tokens per chunk
  chunk_overlap: 200        # Overlap between chunks
  batch_size: 10           # API batch size
  
database:
  similarity_threshold: 0.78 # Minimum similarity for matches
  max_matches: 10           # Maximum results per query

logging:
  level: "INFO"             # DEBUG, INFO, WARNING, ERROR
```

#### Batch Configuration File
```json
[
  {
    "source_path": "./data_sources/perplexity/review.pdf",
    "tool_id": "123e4567-e89b-12d3-a456-426614174000",
    "source_type": "pdf",
    "title": "Perplexity Deep Dive Review"
  },
  {
    "source_path": "https://midjourney.com/docs",
    "tool_id": "987fcdeb-51a2-43d1-9f8e-123456789abc",
    "source_type": "url",
    "title": "Midjourney Documentation"
  }
]
```

## Workflow Examples

### Manual Knowledge Indexing Workflow

Following the RAG-Anything guide workflow:

**Step 1: Identify Target Tool**
```bash
# Find the tool you want to add knowledge for
python run_rag_indexing.py list-tools | grep "Perplexity"
```

**Step 2: Prepare Document**
```bash
# Organize your document
mkdir -p data_sources/perplexity
cp ~/Downloads/perplexity_analysis.pdf data_sources/perplexity/
```

**Step 3: Index Document**
```bash
python run_rag_indexing.py index \
  --tool-id "abc-123-def-456" \
  --source-path "data_sources/perplexity/perplexity_analysis.pdf" \
  --title "Perplexity vs ChatGPT Analysis 2024"
```

**Step 4: Verify Results**
```bash
# Check knowledge was stored
python run_rag_indexing.py stats --tool-id "abc-123-def-456"

# Test improved matching in your web application
# Search for: "AI tool for research and analysis"
# Perplexity should now rank higher due to the new knowledge
```

### Curating High-Quality Knowledge

**Focus on Quality Sources:**
- Official documentation and user guides
- Comparative analysis from reputable tech blogs
- Case studies showing specific use cases
- User reviews highlighting unique features

**Avoid Low-Quality Content:**
- Marketing copy without substance
- Duplicate information already in the system
- Outdated information (check dates)
- Biased or promotional content

### Regular Maintenance

**Monthly Review Process:**
```bash
# 1. Check knowledge statistics for top tools
for tool_id in $(cat important_tools.txt); do
  echo "=== $tool_id ==="
  python run_rag_indexing.py stats --tool-id "$tool_id"
done

# 2. Update outdated knowledge
python run_rag_indexing.py cleanup --tool-id "old-tool-id" --confirm
python run_rag_indexing.py index --tool-id "old-tool-id" --source-path "updated_guide.pdf"

# 3. Add new tools and knowledge as needed
```

## Performance Optimization

### Chunking Strategy
- **Optimal chunk size**: 800-1200 tokens for most content
- **Overlap**: 150-250 tokens to maintain context
- **Quality threshold**: Filter chunks below 100 characters

### Batch Processing
- **Batch size**: 10 documents per batch for API efficiency
- **Rate limiting**: 100ms delay between embedding requests
- **Parallel processing**: Process multiple tools concurrently

### Database Optimization
- **Vector indexing**: Uses IVFFlat with 100 lists for fast similarity search
- **Content indexing**: Full-text search on content for hybrid retrieval
- **Metadata indexing**: Efficient filtering by tool, source type, and status

## Troubleshooting

### Common Issues

**"RAG-Anything not installed" warning:**
```bash
pip install raganything[all]
```

**PDF processing fails:**
```bash
# Install additional dependencies
pip install pdfplumber pypdf2
```

**Memory issues with large documents:**
- Reduce chunk_size in config.yaml
- Process documents one at a time instead of batch
- Monitor system memory usage

**Embedding API rate limits:**
- Increase rate_limit_delay in config.yaml
- Reduce batch_size for processing
- Check Google AI API quotas

### Debug Mode
```bash
python run_rag_indexing.py --verbose index --tool-id "..." --source-path "..."
```

### Log Files
- Application logs: `logs/rag_indexer.log`
- Error details: Check both console output and log files
- Performance metrics: Available in verbose mode

## API Integration

The RAG knowledge chunks are automatically available to the FlowGenius matching system through the database functions:

- `match_rag_knowledge_chunks()`: Find similar chunks for queries
- `get_tool_knowledge_summary()`: Get knowledge overview for tools

### Example Query
```sql
-- Find knowledge chunks similar to a user query
SELECT * FROM match_rag_knowledge_chunks(
  query_embedding := generate_embedding('AI for research tasks'),
  match_threshold := 0.78,
  match_count := 5
);
```

## Future Enhancements

- **Automated crawling**: Periodic updates from official documentation
- **Quality scoring**: ML-based content quality assessment
- **Multi-language support**: Process documents in different languages
- **Real-time updates**: WebSocket notifications for knowledge changes
- **A/B testing**: Compare matching performance with/without RAG knowledge

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is part of FlowGenius and follows the same licensing terms.