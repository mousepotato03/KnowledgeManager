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

### RAG Knowledge Uploader (권장)

GUI를 통해 쉽게 문서를 업로드할 수 있습니다:

```bash
# Windows
scripts\run_rag_gui.bat

# Linux/macOS
./scripts/run_rag_gui.sh
```

### 명령줄 인터페이스

```bash
# 도구 목록 보기
python src/run_rag_indexing.py list-tools

# PDF 문서 업로드
python src/run_rag_indexing.py index --tool-id "도구ID" --source-path "./문서.pdf"

# 웹 URL 업로드
python src/run_rag_indexing.py index --tool-id "도구ID" --source-path "https://example.com" --source-type url

# 도구별 통계 보기
python src/run_rag_indexing.py stats --tool-id "도구ID"
```

### 도구 데이터 임포트

```bash
# 기본 CSV 파일 사용
python src/import_tools_data.py

# 특정 CSV 파일 사용
python src/import_tools_data.py tools_data.csv

# 도움말 보기
python src/import_tools_data.py --help
```

## 프로젝트 구조

```
KnowledgeManager/
├── data/                    # 데이터 파일들
│   └── sample_batch.json    # 배치 처리 샘플 파일
├── scripts/                 # 실행 스크립트들
│   ├── run_rag_gui.bat     # Windows GUI 실행 스크립트
│   ├── run_rag_gui.sh      # Linux/macOS GUI 실행 스크립트
│   ├── run_import.bat      # Windows 데이터 임포트 스크립트
│   └── run_rag_indexing.bat # Windows RAG 인덱싱 스크립트
├── src/                     # 소스 코드
│   ├── rag_gui.py          # GUI 애플리케이션
│   ├── run_rag_indexing.py # CLI 인터페이스
│   ├── rag_indexer.py      # RAG 처리 엔진
│   ├── import_tools_data.py # 도구 데이터 임포트
│   └── config_loader.py    # 설정 로더
├── requirements.txt         # Python 의존성
├── .env                     # 환경변수 (gitignore에 추가)
└── README.md               # 프로젝트 문서
```

## 주요 기능

### 🖥️ GUI 애플리케이션
- 사용자 친화적인 드래그 앤 드롭 인터페이스
- 도구 선택 및 문서 업로드
- 실시간 진행상황 표시
- 통계 및 관리 기능

### 📄 지원 파일 형식
- PDF 문서
- 웹 URL
- 텍스트 파일 (.txt)
- 마크다운 파일 (.md)

### ⚙️ 고급 기능
- 배치 처리 지원
- 청크 크기 조정
- 중복 제거
- 지식 통계 및 관리
