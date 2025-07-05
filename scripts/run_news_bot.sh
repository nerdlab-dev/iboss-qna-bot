#!/bin/bash

# 로그 파일 설정
LOG_FILE="/Users/jaewansim/Documents/nerdlab/bot_cron.log"
ERROR_LOG="/Users/jaewansim/Documents/nerdlab/bot_error.log"

# 시작 시간 기록
echo "=== 봇 실행 시작: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"

# 작업 디렉토리로 이동
cd /Users/jaewansim/Documents/nerdlab
echo "작업 디렉토리: $(pwd)" >> "$LOG_FILE"

# Python 버전 확인
echo "Python 버전: $(python3 --version)" >> "$LOG_FILE"

# 필요한 패키지 확인
echo "설치된 패키지:" >> "$LOG_FILE"
pip3 list >> "$LOG_FILE" 2>&1

# 이전 프로세스 종료
pkill -f "python3 news_bot.py" >> "$LOG_FILE" 2>&1
sleep 2

# 봇 실행
echo "봇 실행 시작..." >> "$LOG_FILE"
python3 news_bot.py >> "$LOG_FILE" 2>&1

# 실행 결과 확인
if [ $? -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 봇 실행 중 오류 발생" >> "$ERROR_LOG"
    echo "상세 오류 로그:" >> "$ERROR_LOG"
    tail -n 50 "$LOG_FILE" >> "$ERROR_LOG"
fi

# 종료 시간 기록
echo "=== 봇 실행 종료: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE" 