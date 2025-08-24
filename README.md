# KnowledgeManager

지식 관리 및 ETL 파이프라인을 위한 Python 기반 시스템입니다.

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
GOOGLE_API_KEY=your_google_api_key
```

## 사용법

### 도구 데이터 임포트

```bash
# 기본 CSV 파일 사용
python import_tools_data.py

# 특정 CSV 파일 사용
python import_tools_data.py tools_data.csv

# 도움말 보기
python import_tools_data.py --help
```

## 프로젝트 구조

```
KnowledgeManager/
├── data/                    # 데이터 파일들
├── scripts/                 # ETL 스크립트들
├── requirements.txt         # Python 의존성
├── .env                     # 환경변수 (gitignore에 추가)
└── README.md               # 프로젝트 문서
```
