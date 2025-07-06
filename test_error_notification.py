#!/usr/bin/env python3
"""
오류 알림 테스트
"""

import requests
from datetime import datetime

# Discord 오류 감지 채널 웹훅
ERROR_WEBHOOK_URL = "https://discord.com/api/webhooks/1391310118850789436/OPWog1Noe8F08Vx19T6Q1TNgo7gMZT7HUQ2czDV-WZ8dhfDXKLmFOHhCM-Ydcbd4ikur"

def test_error_notification():
    """테스트 오류 알림 전송"""
    
    embed = {
        "title": "🧪 테스트: 크롤러 오류 알림",
        "description": "이것은 오류 알림 시스템 테스트입니다.",
        "color": 16776960,  # 노란색
        "fields": [
            {
                "name": "테스트 항목",
                "value": "Discord 웹훅 연결 확인",
                "inline": True
            },
            {
                "name": "전송 시간",
                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "inline": True
            },
            {
                "name": "예상 오류 알림",
                "value": "• 크롤링 실패 시\n• 로그 파일 오류 시\n• 데이터 파일 문제 시\n• 실행 시간 초과 시",
                "inline": False
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "footer": {
            "text": "크롤러 모니터링 시스템 테스트"
        }
    }
    
    data = {
        "embeds": [embed],
        "username": "크롤러 모니터링 (테스트)"
    }
    
    try:
        response = requests.post(ERROR_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("✅ 테스트 알림 전송 성공!")
            print("Discord 오류 감지 채널을 확인하세요.")
        else:
            print(f"❌ 전송 실패: {response.status_code}")
            print(f"응답: {response.text}")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_error_notification()