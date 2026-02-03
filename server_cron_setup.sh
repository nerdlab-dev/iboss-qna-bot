#!/bin/bash
# 서버 크론탭 설정 스크립트

# 크론탭 엔트리 추가
(crontab -l 2>/dev/null; echo "0 8 * * * cd /home/nerdlab-datastudio-python && /home/nerdlab-datastudio-python/news-venv/bin/python /home/nerdlab-datastudio-python/src/server_news_bot.py >> /home/nerdlab-datastudio-python/news_cron.log 2>&1") | crontab -

echo "크론탭 설정 완료. 매일 오전 8시에 뉴스 봇이 실행됩니다."
crontab -l