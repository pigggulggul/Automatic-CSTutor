# Notion CS Tutor Automation

매일 자동으로 Notion에 CS 지식을 업데이트하는 시스템입니다.

## 🔒 보안 주의사항

**절대 .env 파일을 Git에 올리지 마세요!**

- `.env` 파일은 `.gitignore`에 포함되어 있습니다
- `.env.example` 파일을 복사하여 본인의 API 키를 입력하세요

## 📋 설정 방법

1. `.env.example` 파일을 `.env`로 복사
2. `.env` 파일에 본인의 API 키를 입력
3. `requirements.txt` 설치: `pip install -r requirements.txt`
4. 스크립트 실행: `python main.py`

## 🚀 GitHub Actions 자동화

현재 프로젝트는 GitHub Actions를 통한 자동화를 실행합니다.

## 📝 파일 설명

- `main.py`: 메인 실행 파일
- `verify_notion.py`: Notion API 연결 테스트
- `list_models.py`: Gemini 모델 목록 확인
- `.env.example`: 환경변수 예시 파일
- `requirements.txt`: 필요한 Python 패키지
