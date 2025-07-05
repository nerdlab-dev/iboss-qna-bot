#!/bin/bash

# 현재 crontab 백업
echo "현재 crontab을 백업합니다..."
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# 새로운 cron job 추가
echo "새로운 cron job을 추가합니다..."

# 현재 crontab 내용을 가져오고 (없으면 빈 상태로), 새 job 추가
(crontab -l 2>/dev/null; echo "# 아이보스 질문답변 봇 - 매일 오전 9시 실행") | crontab -
(crontab -l 2>/dev/null; echo "0 9 * * * cd /Users/jaewansim/Documents/nerdlab/news-crawler-bot && /usr/bin/python3 src/iboss_qna_bot.py >> logs/cron.log 2>&1") | crontab -

echo "Cron job이 추가되었습니다."
echo ""
echo "현재 crontab 내용:"
crontab -l

echo ""
echo "로그 파일 위치: /Users/jaewansim/Documents/nerdlab/news-crawler-bot/logs/cron.log"
echo ""
echo "cron job을 제거하려면: crontab -e 후 해당 라인 삭제"