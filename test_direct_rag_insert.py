#!/usr/bin/env python3

import os
import json
import hashlib
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
import uuid

# Load environment variables
load_dotenv('../workflow-ai/.env.local')

# Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# Sample Perplexity AI knowledge chunks
perplexity_knowledge = [
    {
        "content": """Perplexity AI는 실시간 웹 검색을 통합한 차세대 AI 검색 엔진으로, 기존 ChatGPT나 Claude와는 차별화된 연구 중심의 AI 도구입니다. 
        
핵심 특징:
- 실시간 정보 접근: 최신 정보를 실시간으로 검색하여 답변에 반영
- 인용 및 출처 제공: 모든 답변에 명확한 출처와 링크 제공  
- 팩트 체킹 강화: 여러 신뢰할 수 있는 소스를 cross-reference
- Focus 모드: Academic, Writing, Wolfram Alpha 등 특화된 검색""",
        "title": "Perplexity AI 개요 및 핵심 특징"
    },
    {
        "content": """Perplexity AI의 실용적 사용 사례:

연구 및 분석 작업:
- 최신 기술 트렌드 조사
- 경쟁사 분석 및 시장 동향 파악
- 학술 논문 및 연구 자료 검색
- 정책 변화 및 규제 동향 모니터링

콘텐츠 제작 지원:
- 블로그 포스트 및 아티클 작성 지원
- 프레젠테이션 자료 수집 및 정리
- 마케팅 캠페인 리서치

의사결정 지원:
- 투자 결정을 위한 시장 분석
- 제품 출시 전 시장 조사""",
        "title": "Perplexity AI 실용 사용 사례"
    },
    {
        "content": """Perplexity AI vs 다른 AI 도구 비교:

vs ChatGPT:
- 실시간 정보: Perplexity 강함 / ChatGPT 제한적
- 출처 제공: Perplexity 모든 답변 / ChatGPT 없음
- 연구 특화: Perplexity 매우 강함 / ChatGPT 보통
- 창작 능력: Perplexity 보통 / ChatGPT 매우 강함

vs Google Search:
- 정보 종합: Perplexity AI가 종합 분석 / Google은 사용자가 직접
- 즉시 답변: Perplexity 바로 제공 / Google 클릭 필요
- 심층 분석: Perplexity 강함 / Google 제한적""",
        "title": "Perplexity AI 경쟁 도구 비교"
    },
    {
        "content": """Perplexity AI 성능 및 비용 효율성:

강점:
1. 최신성: 실시간 정보 접근으로 최신 데이터 제공
2. 신뢰성: 출처 명시로 팩트 체킹 가능
3. 효율성: 여러 소스를 한 번에 종합 분석
4. 전문성: Focus 모드로 특화된 검색 가능

비용 효율성:
- Pro 구독 ($20/월) 가치 평가
- 전통적 리서치 시간: 4-6시간 → Perplexity 활용: 30분-1시간
- 시간 절약: 75-85%
- 월 20시간 리서치 기준: 약 15시간 절약, 시급 50달러 기준 월 750달러 가치

추천 사용자: 연구원, 애널리스트, 컨설턴트, 콘텐츠 크리에이터, 투자자""",
        "title": "Perplexity AI 성능 분석 및 ROI"
    }
]

def generate_embedding(text: str) -> list:
    """Generate embedding using Google's text-embedding-004 model"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="Perplexity AI Knowledge"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def insert_rag_chunk(tool_id: str, chunk_data: dict, chunk_index: int) -> bool:
    """Insert a RAG knowledge chunk into the database"""
    
    # Generate embedding
    embedding = generate_embedding(chunk_data['content'])
    if not embedding:
        print(f"Failed to generate embedding for chunk {chunk_index}")
        return False
    
    # Create content hash
    content_hash = hashlib.md5(chunk_data['content'].encode()).hexdigest()
    
    # Prepare data for insertion
    chunk_record = {
        'id': str(uuid.uuid4()),
        'tool_id': tool_id,
        'chunk_content': chunk_data['content'],
        'chunk_type': 'text',
        'source_path': 'data_sources/perplexity_analysis.md',
        'source_title': chunk_data['title'],
        'source_type': 'guide',
        'chunk_index': chunk_index,
        'content_hash': content_hash,
        'quality_score': 0.9,
        'total_chunks': len(perplexity_knowledge),
        'embedding': embedding,
        'chunk_metadata': {
            'processing_version': '1.0',
            'generated_by': 'manual_script',
            'embedding_model': 'text-embedding-004'
        }
    }
    
    try:
        result = supabase.table('rag_knowledge_chunks').insert(chunk_record).execute()
        print(f"Successfully inserted chunk {chunk_index}: {chunk_data['title'][:50]}...")
        return True
    except Exception as e:
        print(f"Failed to insert chunk {chunk_index}: {e}")
        return False

def main():
    # Perplexity AI tool ID
    perplexity_tool_id = '89bce0bb-80cf-431f-88ed-3b14ee8ba24a'
    
    print("Starting RAG knowledge insertion for Perplexity AI...")
    print(f"Total chunks to process: {len(perplexity_knowledge)}")
    
    successful_inserts = 0
    
    for i, chunk in enumerate(perplexity_knowledge, 1):
        print(f"\nProcessing chunk {i}/{len(perplexity_knowledge)}")
        if insert_rag_chunk(perplexity_tool_id, chunk, i):
            successful_inserts += 1
    
    print(f"\nRAG insertion completed!")
    print(f"Successfully inserted: {successful_inserts}/{len(perplexity_knowledge)} chunks")
    
    if successful_inserts > 0:
        print(f"\nNow testing the Advanced Hybrid Search...")
        # Test query
        test_query = "AI tool for research and analysis"
        print(f"Test query: '{test_query}'")
        
        # You would need to run this from the Next.js app or call the advanced_hybrid_search function

if __name__ == "__main__":
    main()