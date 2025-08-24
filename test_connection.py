#!/usr/bin/env python3
"""
연결 테스트 스크립트
Supabase와 Google AI 연결 상태를 확인합니다.
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def test_environment():
    """환경변수 설정 확인"""
    print("🔍 환경변수 설정 확인 중...")
    
    required_vars = [
        "NEXT_PUBLIC_SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY", 
        "GOOGLE_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: {value[:20]}...")
    
    if missing_vars:
        print(f"  ❌ 누락된 환경변수: {', '.join(missing_vars)}")
        return False
    
    print("  ✅ 모든 환경변수가 설정되었습니다.")
    return True

def test_supabase_connection():
    """Supabase 연결 테스트"""
    try:
        from supabase import create_client, Client
        
        print("\n🔍 Supabase 연결 테스트 중...")
        
        supabase: Client = create_client(
            os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        )
        
        # 간단한 쿼리 테스트
        result = supabase.table("tools").select("count", count="exact").execute()
        print("  ✅ Supabase 연결 성공")
        return True
        
    except Exception as e:
        print(f"  ❌ Supabase 연결 실패: {str(e)}")
        return False

def test_google_ai():
    """Google AI 연결 테스트"""
    try:
        import google.generativeai as genai
        
        print("\n🔍 Google AI 연결 테스트 중...")
        
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("text-embedding-004")
        
        # 간단한 임베딩 테스트
        test_text = "Hello, World!"
        result = model.embed_content(test_text)
        
        if result.embedding.values:
            print("  ✅ Google AI 연결 성공")
            return True
        else:
            print("  ❌ Google AI 임베딩 생성 실패")
            return False
            
    except Exception as e:
        print(f"  ❌ Google AI 연결 실패: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 KnowledgeManager 연결 테스트 시작\n")
    
    # 환경변수 확인
    env_ok = test_environment()
    if not env_ok:
        print("\n❌ 환경변수 설정이 완료되지 않았습니다.")
        print("env.example 파일을 .env로 복사하고 필요한 값을 설정하세요.")
        return
    
    # Supabase 연결 테스트
    supabase_ok = test_supabase_connection()
    
    # Google AI 연결 테스트
    google_ok = test_google_ai()
    
    # 최종 결과
    print("\n📊 테스트 결과:")
    if supabase_ok and google_ok:
        print("🎉 모든 연결이 성공했습니다!")
        print("ETL 스크립트를 실행할 수 있습니다.")
    else:
        print("⚠️  일부 연결에 문제가 있습니다.")
        print("위의 오류 메시지를 확인하고 수정하세요.")

if __name__ == "__main__":
    main()
