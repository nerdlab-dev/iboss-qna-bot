#!/bin/bash
# Q&A 봇 크론탭 추가 스크립트

# 크론탭 엔트리 추가 (오후 6시)
(crontab -l 2>/dev/null; echo "0 18 * * * cd /home/nerdlab-datastudio-python && /home/nerdlab-datastudio-python/news-venv/bin/python /home/nerdlab-datastudio-python/src/server_qna_bot.py >> /home/nerdlab-datastudio-python/qna_cron.log 2>&1") | crontab -

echo "Q&A 봇 크론탭 설정 완료. 매일 오후 6시에 실행됩니다."
crontab -l | tail -5