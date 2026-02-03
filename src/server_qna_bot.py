#!/usr/bin/env python3
"""
서버용 Q&A 크롤링 봇 - Discord 웹훅 버전
"""

import os
import sys
import requests
from datetime import datetime
import logging

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 서버용 Chrome 드라이버 설정
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def get_chrome_driver():
    """서버용 Chrome 웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 서버에서는 chromium-driver 직접 사용
    service = Service('/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=chrome_options)

# Q&A 봇의 함수들을 import
from src.iboss_qna_bot import get_qna_posts, load_last_posts, save_last_posts

# get_chrome_driver 함수를 서버용으로 오버라이드
import src.iboss_qna_bot
src.iboss_qna_bot.get_chrome_driver = get_chrome_driver

# Discord 웹훅 URL (Q&A 채널용)
QNA_WEBHOOK_URL = "https://discord.com/api/webhooks/1390991646140665896/Y9Qs_o7L0Yd0mQWBIrVZmFP4rRV7Xs5OQBR_t_X112qhO3hgeOXKaqKq65s18RntDF_N"

def send_qna_to_discord_webhook(posts):
    """Discord 웹훅으로 Q&A 전송"""
    if not posts:
        logger.info("전송할 새로운 질문이 없습니다.")
        return
    
    logger.info(f"{len(posts)}개의 새로운 질문을 전송합니다.")
    
    # 임베드 생성
    embeds = []
    
    # 메인 임베드
    main_embed = {
        "title": "📢 아이보스 새로운 질문",
        "description": f"{len(posts)}개의 새로운 질문이 등록되었습니다.",
        "color": 3447003,  # 파란색
        "timestamp": datetime.now().isoformat(),
        "fields": [],
        "footer": {
            "text": "아이보스 질문답변 게시판"
        }
    }
    
    # 최대 3개까지만 표시
    for i, post in enumerate(posts[:3]):
        field_value = ""
        if post.get('content'):
            field_value += f"{post['content'][:100]}...\n"
        if post.get('author'):
            field_value += f"작성자: {post['author']}"
        if post.get('date'):
            field_value += f" | {post['date']}"
        field_value += f"\n[자세히 보기]({post['link']})"
        
        # 제목이 너무 길면 잘라내기
        title = post['title']
        if len(title) > 250:
            title = title[:247] + "..."
        
        main_embed["fields"].append({
            "name": f"{i+1}. {title}",
            "value": field_value,
            "inline": False
        })
    
    if len(posts) > 3:
        main_embed["fields"].append({
            "name": "추가 질문",
            "value": f"외 {len(posts)-3}개의 질문이 더 있습니다.",
            "inline": False
        })
    
    embeds.append(main_embed)
    
    # 웹훅 전송
    data = {
        "embeds": embeds,
        "username": "아이보스 Q&A 봇"
    }
    
    try:
        response = requests.post(QNA_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logger.info("디스코드 전송 성공")
        else:
            logger.error(f"디스코드 전송 실패: {response.status_code}")
            logger.error(f"응답: {response.text}")
    except Exception as e:
        logger.error(f"디스코드 전송 오류: {str(e)}")

def check_and_send_qna():
    """새로운 Q&A 확인 및 전송"""
    # 기존 게시물 ID 로드
    last_post_ids = load_last_posts()
    
    # 새로운 게시물 크롤링
    posts = get_qna_posts()
    
    if not posts:
        logger.info("크롤링된 게시물이 없습니다.")
        return
    
    # 새로운 게시물만 필터링
    new_posts = []
    current_post_ids = []
    
    for post in posts:
        current_post_ids.append(post['id'])
        if post['id'] not in last_post_ids:
            new_posts.append(post)
    
    # 새로운 게시물 전송
    if new_posts:
        send_qna_to_discord_webhook(new_posts)
    else:
        logger.info("새로운 질문이 없습니다.")
        # 첫 실행이면 최신 3개만 전송
        if not last_post_ids and posts:
            send_qna_to_discord_webhook(posts[:3])
    
    # 현재 게시물 ID 저장
    save_last_posts(current_post_ids[:10])

if __name__ == "__main__":
    try:
        logger.info("서버 Q&A 크롤링 시작")
        check_and_send_qna()
        logger.info("서버 Q&A 크롤링 완료")
    except Exception as e:
        logger.error(f"서버 크롤링 오류: {str(e)}")
        import traceback
        traceback.print_exc()