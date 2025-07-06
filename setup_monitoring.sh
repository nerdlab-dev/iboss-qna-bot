#!/bin/bash
# 크롤러 모니터링 크론탭 설정

echo "크롤러 모니터링 설정 중..."

# 모니터링 크론탭 추가
(crontab -l 2>/dev/null; echo "# 크롤러 모니터링 - 매시간 실행") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * cd /home/nerdlab-datastudio-python && /home/nerdlab-datastudio-python/news-venv/bin/python /home/nerdlab-datastudio-python/src/crawler_monitor.py >> /home/nerdlab-datastudio-python/crawler_monitor.log 2>&1") | crontab -

echo "모니터링 크론탭 설정 완료"
echo ""
echo "설정된 크론탭:"
crontab -l | grep -E "(adaptive_|crawler_monitor)"
echo ""
echo "모니터링 기능:"
echo "- 매시간 크롤러 상태 체크"
echo "- 오류 발생 시 Discord 알림"
echo "- 로그 파일 및 데이터 파일 검증"
echo "- 실행 시간 초과 감지"