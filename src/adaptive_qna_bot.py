#!/usr/bin/env python3
"""
적응형 Q&A 크롤링 봇 - HTML 구조 변경 자동 대응
"""

import os
import sys
import requests
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

from src.html_structure_validator import HTMLStructureValidator, create_adaptive_crawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Discord 웹훅 URL
QNA_WEBHOOK_URL = "https://discord.com/api/webhooks/1390991646140665896/Y9Qs_o7L0Yd0mQWBIrVZmFP4rRV7Xs5OQBR_t_X112qhO3hgeOXKaqKq65s18RntDF_N"

# 마지막 Q&A 저장 파일
LAST_POST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_qna_adaptive.json')

def get_chrome_driver():
    """Chrome 웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 서버인지 로컬인지 확인
    if os.path.exists('/usr/bin/chromedriver'):
        # 서버에서는 chromium-driver 직접 사용
        service = Service('/usr/bin/chromedriver')
    else:
        # 로컬에서는 webdriver-manager 사용
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    
    return webdriver.Chrome(service=service, options=chrome_options)

def get_qna_adaptive():
    """적응형 Q&A 크롤링"""
    driver = None
    validator = HTMLStructureValidator()
    
    try:
        driver = get_chrome_driver()
        
        # Q&A 페이지 접속
        logger.info("Q&A 페이지 접속")
        driver.get("https://www.i-boss.co.kr/ab-2109")
        time.sleep(5)
        
        # HTML 구조 검증
        html = driver.page_source
        validation_result = validator.validate_and_update(html, 'qna')
        
        if not validation_result['valid']:
            logger.error("유효한 Q&A를 찾을 수 없습니다")
            # 디버그용 HTML 저장
            with open('qna_debug_adaptive.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return []
        
        logger.info(f"HTML 구조 검증 완료: {validation_result['items_found']}개 항목 발견")
        logger.info(f"최적 패턴: {validation_result['best_pattern']}")
        
        if validation_result['needs_update']:
            logger.info("HTML 구조 변경 감지 - 새로운 패턴으로 업데이트")
        
        # 적응형 추출
        soup = BeautifulSoup(html, 'html.parser')
        adaptive_extractor = create_adaptive_crawler('qna', validator)
        posts = adaptive_extractor(soup)
        
        logger.info(f"총 {len(posts)}개의 Q&A 추출 완료")
        
        # 추가 정보 보강
        for post in posts[:10]:  # 최신 10개만
            # 작성자 정보 추가 시도
            parent = soup.find(text=post['title'])
            if parent:
                parent_elem = parent.parent.parent if parent.parent else None
                if parent_elem:
                    info_elem = parent_elem.select_one('.info, .author, .meta')
                    if info_elem:
                        info_text = info_elem.get_text(strip=True)
                        if '|' in info_text:
                            parts = info_text.split('|')
                            post['author'] = parts[0].strip()
                            post['date'] = parts[-1].strip()
            
            # 내용 미리보기 추가
            if not post.get('content'):
                post['content'] = post['title'][:200] + '...' if len(post['title']) > 200 else post['title']
        
        return posts[:10]
        
    except Exception as e:
        logger.error(f"크롤링 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            driver.quit()

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
            "text": "아이보스 질문답변 게시판 (적응형)"
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
        "username": "아이보스 Q&A 봇 (적응형)"
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
    last_post_ids = []
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, 'r') as f:
            last_post_ids = json.load(f)
    
    # 새로운 게시물 크롤링
    posts = get_qna_adaptive()
    
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
    with open(LAST_POST_FILE, 'w') as f:
        json.dump(current_post_ids[:10], f)

if __name__ == "__main__":
    try:
        logger.info("적응형 Q&A 크롤링 시작")
        check_and_send_qna()
        logger.info("적응형 Q&A 크롤링 완료")
    except Exception as e:
        logger.error(f"크롤링 오류: {str(e)}")
        import traceback
        traceback.print_exc()