#!/bin/bash
# 적응형 봇으로 크론탭 업데이트

# 기존 크론탭 백업
crontab -l > cron_backup.txt

# 기존 뉴스/Q&A 크론탭 제거
crontab -l | grep -v "server_news_bot.py" | grep -v "server_qna_bot.py" > temp_cron.txt

# 적응형 봇 크론탭 추가
echo "# 적응형 뉴스 봇 - 매일 오전 8시" >> temp_cron.txt
echo "0 8 * * * cd /home/nerdlab-datastudio-python && /home/nerdlab-datastudio-python/news-venv/bin/python /home/nerdlab-datastudio-python/src/adaptive_news_bot.py >> /home/nerdlab-datastudio-python/adaptive_news_cron.log 2>&1" >> temp_cron.txt
echo "" >> temp_cron.txt
echo "# 적응형 Q&A 봇 - 매일 오후 6시" >> temp_cron.txt
echo "0 18 * * * cd /home/nerdlab-datastudio-python && /home/nerdlab-datastudio-python/news-venv/bin/python /home/nerdlab-datastudio-python/src/adaptive_qna_bot.py >> /home/nerdlab-datastudio-python/adaptive_qna_cron.log 2>&1" >> temp_cron.txt

# 새로운 크론탭 설치
crontab temp_cron.txt
rm temp_cron.txt

echo "적응형 봇 크론탭 업데이트 완료"
echo "현재 크론탭:"
crontab -l | tail -10