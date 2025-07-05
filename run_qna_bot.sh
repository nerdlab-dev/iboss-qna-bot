#!/bin/bash

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (있다면)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 환경변수 확인
if [ ! -f ".env" ]; then
    echo "Error: .env 파일이 없습니다. .env.example을 참고하여 .env 파일을 생성해주세요."
    exit 1
fi

# 로그 디렉토리 생성
mkdir -p logs

# 봇 실행
echo "아이보스 질문답변 봇을 시작합니다..."
python src/iboss_qna_bot.py