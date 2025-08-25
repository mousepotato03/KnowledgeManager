# RAG Indexing Quick Start Guide

Get up and running with RAG knowledge indexing in 5 minutes.

## Prerequisites Checklist
- [ ] Python 3.8+ installed
- [ ] Supabase project with vector extension enabled
- [ ] Google AI API key
- [ ] Access to FlowGenius database

## 1. Environment Setup (2 minutes)

**Install dependencies:**
```bash
# Windows
run_rag_indexing.bat list-tools

# Linux/macOS
./run_rag_indexing.sh list-tools
```

## 2. Database Migration (1 minute)

1. Open your Supabase SQL editor
2. Copy the contents of `workflow-ai/supabase/migrations/20250824000001_add_rag_knowledge_chunks.sql`
3. Run the migration
4. Verify the `rag_knowledge_chunks` table was created

## 3. Your First Knowledge Index (2 minutes)

**Step 1: Find a tool to enhance**
```bash
python run_rag_indexing.py list-tools
```
Copy a tool ID from the output (e.g., `12345678-1234-1234-1234-123456789abc`).

**Step 2: Create a simple text file**
```bash
mkdir -p data_sources/test_tool
echo "This amazing tool is perfect for data analysis tasks. It excels at processing large datasets and generating insightful reports. Data scientists love using it for complex statistical analysis." > data_sources/test_tool/knowledge.txt
```

**Step 3: Index the knowledge**
```bash
python run_rag_indexing.py index \
  --tool-id "12345678-1234-1234-1234-123456789abc" \
  --source-path "data_sources/test_tool/knowledge.txt" \
  --title "Tool Knowledge Example"
```

**Step 4: Verify it worked**
```bash
python run_rag_indexing.py stats --tool-id "12345678-1234-1234-1234-123456789abc"
```

You should see:
```
📊 Knowledge Statistics for Tool: 12345678-1234-1234-1234-123456789abc
   • Total chunks: 1
   • Sources:
     - Tool Knowledge Example (text) - 1 chunks
   • Top content samples:
     1. [0.7] This amazing tool is perfect for data analysis tasks. It excels at processing large...
```

## 4. Test the Impact

Go to your FlowGenius web application and search for:
- "data analysis tool"
- "statistical analysis software"
- "dataset processing"

The tool you just added knowledge for should now appear higher in the results!

## Next Steps

### Add Real Knowledge
Replace the test file with actual valuable content:

**High-value sources:**
- Official user guides (PDF)
- Detailed blog post reviews
- Comparison articles
- Case studies

**Example with PDF:**
```bash
# Download a guide or review
python run_rag_indexing.py index \
  --tool-id "your-tool-id" \
  --source-path "path/to/comprehensive_guide.pdf" \
  --title "Official User Guide v2.1"
```

**Example with web article:**
```bash
python run_rag_indexing.py index \
  --tool-id "your-tool-id" \
  --source-path "https://blog.techreview.com/tool-deep-dive-2024" \
  --source-type "url" \
  --title "Tech Review Deep Dive 2024"
```

### Batch Processing
Create `my_batch.json`:
```json
[
  {
    "source_path": "./guides/tool1_guide.pdf",
    "tool_id": "tool1-uuid-here",
    "source_type": "pdf",
    "title": "Tool 1 Official Guide"
  },
  {
    "source_path": "https://example.com/tool2-review",
    "tool_id": "tool2-uuid-here", 
    "source_type": "url",
    "title": "Tool 2 Expert Review"
  }
]
```

Run batch processing:
```bash
python run_rag_indexing.py batch --batch-file "my_batch.json"
```

### Monitor and Maintain
```bash
# Check knowledge stats for all your important tools
python run_rag_indexing.py stats --tool-id "tool-1-id"
python run_rag_indexing.py stats --tool-id "tool-2-id"

# Clean up old knowledge when needed
python run_rag_indexing.py cleanup --tool-id "tool-id" --source-path "old_guide.pdf" --confirm
```

## Troubleshooting

**Can't find tools?**
- Verify your Supabase connection
- Check that the `tools` table has data
- Ensure your service role key has read access

**Embedding generation fails?**
- Verify Google AI API key is valid
- Check API quotas and billing
- Try with smaller documents first

**No impact on search results?**
- Wait a few minutes for cache refresh
- Try more specific search terms
- Add more comprehensive knowledge content

**Need help?**
- Check the full `README_RAG.md` for detailed documentation
- Look at log files in `logs/rag_indexer.log`
- Use `--verbose` flag for detailed debugging

## Success Criteria

You'll know it's working when:
1. ✅ Commands run without errors
2. ✅ Knowledge chunks are stored in the database
3. ✅ Statistics show your content
4. ✅ Search results improve for your tools

Happy indexing! 🚀