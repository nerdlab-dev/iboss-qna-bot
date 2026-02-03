#!/bin/bash

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 로그 디렉토리 생성
mkdir -p logs

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 환경변수 확인
if [ ! -f ".env" ]; then
    echo "Error: .env 파일이 없습니다."
    exit 1
fi

# 실행 시간 로그
echo "========================================" >> logs/daily_cron.log
echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> logs/daily_cron.log
echo "========================================" >> logs/daily_cron.log

# 봇 실행
python src/iboss_daily_bot.py >> logs/daily_cron.log 2>&1

# 실행 결과
if [ $? -eq 0 ]; then
    echo "크롤링 완료: $(date '+%Y-%m-%d %H:%M:%S')" >> logs/daily_cron.log
else
    echo "크롤링 실패: $(date '+%Y-%m-%d %H:%M:%S')" >> logs/daily_cron.log
fi