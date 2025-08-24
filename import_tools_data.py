#!/usr/bin/env python3
"""
도구 데이터 임포트 ETL 스크립트
TypeScript 버전을 Python으로 변환한 버전
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import pandas as pd
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 클라이언트 초기화
supabase: Client = create_client(
    os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
)

# Google AI 설정
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
embedding_model = genai.GenerativeModel("text-embedding-004")

# CSV 스키마 인터페이스 - 실제 DB 컬럼에 맞춤
class ToolCsvRow:
    def __init__(self, row: Dict[str, str]):
        self.name = row.get("name", "")
        self.description = row.get("description", "")
        self.url = row.get("url", "")
        self.logo_url = row.get("logo_url", "")
        self.categories = row.get("categories", "")
        self.domains = row.get("domains", "")
        self.scores = row.get("scores", "")
        self.embedding_text = row.get("embedding_text", "")

def ensure_array(csv_field: Optional[str]) -> List[str]:
    """CSV 필드를 배열로 변환"""
    if not csv_field:
        return []
    return [s.strip() for s in csv_field.split(",") if s.strip()]

def build_favicon_url(url_str: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
    """URL에서 파비콘 URL 생성"""
    try:
        if not url_str and fallback:
            url_str = fallback
        if not url_str:
            return None
        
        parsed_url = urlparse(url_str)
        return f"https://www.google.com/s2/favicons?domain={parsed_url.netloc}&sz=128"
    except:
        return None

def parse_scores(json_like: Optional[str]) -> Dict[str, Any]:
    """JSON 문자열을 파싱하여 scores 딕셔너리 반환"""
    if not json_like or json_like.strip() == "":
        return {}
    try:
        return json.loads(json_like)
    except:
        return {}

def import_tools_from_csv(csv_file_name: str) -> None:
    """CSV 파일에서 도구 데이터 임포트"""
    print(f"\n🔧 Import: {csv_file_name} ...")
    
    csv_file_path = Path(__file__).parent / "data" / csv_file_name
    
    if not csv_file_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
    
    # CSV 파일 읽기
    records = []
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        records = [ToolCsvRow(row) for row in reader]
    
    print(f"📊 총 {len(records)}개의 도구 데이터를 읽었습니다.")
    
    success = 0
    failed = 0
    
    for i, row in enumerate(records):
        try:
            print(f"\n⚙️  [{i + 1}/{len(records)}] \"{row.name}\" 처리 중...")
            
            categories = ensure_array(row.categories)
            domains = ensure_array(row.domains)
            scores = parse_scores(row.scores)
            computed_logo = build_favicon_url(row.url, row.logo_url)
            logo_url = row.logo_url if row.logo_url and row.logo_url.strip() else computed_logo
            
            print("  🧠 임베딩 생성 중...")
            
            # Google AI 임베딩 생성
            embedding_result = embedding_model.embed_content(row.embedding_text)
            embedding = embedding_result.embedding.values
            
            # 데이터베이스에 저장
            data = {
                "name": row.name,
                "description": row.description or None,
                "url": row.url or None,
                "logo_url": logo_url,
                "categories": categories,
                "domains": domains,
                "embedding_text": row.embedding_text,
                "embedding": embedding,
                "is_active": True,
                "scores": scores
            }
            
            result = supabase.table("tools").upsert(
                data,
                on_conflict="name"
            ).execute()
            
            if result.data:
                print(f"  ✅ \"{row.name}\" 저장 완료")
                success += 1
            else:
                raise Exception("저장 실패")
                
        except Exception as e:
            print(f"  ❌ \"{row.name}\" 처리 실패: {str(e)}")
            failed += 1
        
        # API 레이트 리밋 방지
        if i < len(records) - 1:
            time.sleep(0.08)
    
    print(f"\n📈 Import 완료 — 성공: {success}, 실패: {failed}")

def import_tools_data(csv_file_name: Optional[str] = None) -> None:
    """메인 임포트 함수"""
    try:
        # 기본 파일명 설정
        default_file_name = "20250822000001_tools_data.csv"
        file_name = csv_file_name or default_file_name
        
        print("🚀 도구 데이터 가져오기 시작...")
        print(f"📋 파일: {file_name}")
        
        import_tools_from_csv(file_name)
        
        # 최종 통계 확인
        print("\n📊 최종 통계 확인...")
        result = supabase.table("tools").select("*", count="exact").execute()
        
        if result.data is not None:
            tools_count = len(result.data)
            print(f"🗄️  도구 수: {tools_count}개")
            print("🎯 임베딩 및 scores 저장 완료!")
        else:
            print("❌ 통계 조회 실패")
            
    except Exception as error:
        print(f"❌ 가져오기 프로세스 오류: {str(error)}")
        sys.exit(1)

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="도구 데이터 임포트 스크립트")
    parser.add_argument("csv_file", nargs="?", help="CSV 파일명 (기본값: 20250822000001_tools_data.csv)")
    parser.add_argument("--help", "-h", action="store_true", help="도움말 표시")
    
    args = parser.parse_args()
    
    if args.help:
        print("""
📚 도구 데이터 가져오기 스크립트 사용법:

기본 사용법:
  python import_tools_data.py                    # 기본 파일 (20250822000001_tools_data.csv) 사용
  python import_tools_data.py [파일명.csv]       # 특정 CSV 파일 사용

예시:
  python import_tools_data.py
  python import_tools_data.py my_tools.csv
  python import_tools_data.py 20250822000001_tools_data.csv

도움말:
  python import_tools_data.py --help
  python import_tools_data.py -h
        """)
        return
    
    import_tools_data(args.csv_file)

if __name__ == "__main__":
    main()
