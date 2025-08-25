#!/bin/bash

echo "🚀 KnowledgeManager ETL 스크립트 실행"
echo

# 환경변수 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다."
    echo "env.example 파일을 .env로 복사하고 환경변수를 설정하세요."
    exit 1
fi

# Python 스크립트 실행
python3 import_tools_data.py "$@"

echo
echo "✅ 스크립트 실행 완료"
