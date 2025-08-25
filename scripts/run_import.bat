@echo off
echo 🚀 KnowledgeManager ETL 스크립트 실행
echo.

REM 환경변수 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다.
    echo env.example 파일을 .env로 복사하고 환경변수를 설정하세요.
    pause
    exit /b 1
)

REM Python 스크립트 실행
python import_tools_data.py %*

echo.
echo ✅ 스크립트 실행 완료
pause
