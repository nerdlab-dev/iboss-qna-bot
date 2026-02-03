#!/usr/bin/env python3
"""
적응형 뉴스 크롤링 봇 - HTML 구조 변경 자동 대응
"""

import os
import sys
import requests
from datetime import datetime
import logging
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

from src.html_structure_validator import HTMLStructureValidator, create_adaptive_crawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Discord 웹훅 URL
NEWS_WEBHOOK_URL = "https://discord.com/api/webhooks/1391000157872590919/YGKb11bk4MCyIjJVh4fQzVHNOWAF50jPmnmsFD2xhtQffJ8AKnID5FgAwe0l32-MoD_3"

# 마지막 뉴스 저장 파일
LAST_NEWS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_news_adaptive.json')

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

def login_to_iboss(driver):
    """아이보스 로그인"""
    try:
        logger.info("아이보스 로그인 시작")
        driver.get("https://www.i-boss.co.kr/ab-login")
        time.sleep(3)
        
        wait = WebDriverWait(driver, 10)
        
        # 로그인 필드 찾기
        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='user_id']")))
        email_input.clear()
        email_input.send_keys("shane@rebeltech.info")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys("project123!@")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        login_button.click()
        
        time.sleep(5)
        
        current_url = driver.current_url
        if "ab-login" not in current_url:
            logger.info("로그인 성공")
            return True
        else:
            logger.error("로그인 실패")
            return False
            
    except Exception as e:
        logger.error(f"로그인 중 오류: {str(e)}")
        return False

def get_news_adaptive():
    """적응형 뉴스 크롤링"""
    driver = None
    validator = HTMLStructureValidator()
    
    try:
        driver = get_chrome_driver()
        
        # 로그인
        if not login_to_iboss(driver):
            logger.error("로그인 실패로 크롤링 중단")
            return []
        
        # 뉴스 페이지 접속
        logger.info("뉴스 페이지 접속")
        driver.get("https://www.i-boss.co.kr/ab-7214")
        time.sleep(5)
        
        # 페이지 스크롤
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        # HTML 구조 검증
        html = driver.page_source
        validation_result = validator.validate_and_update(html, 'news')
        
        if not validation_result['valid']:
            logger.error("유효한 뉴스를 찾을 수 없습니다")
            # 디버그용 HTML 저장
            with open('news_debug_adaptive.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return []
        
        logger.info(f"HTML 구조 검증 완료: {validation_result['items_found']}개 항목 발견")
        logger.info(f"최적 패턴: {validation_result['best_pattern']}")
        
        if validation_result['needs_update']:
            logger.info("HTML 구조 변경 감지 - 새로운 패턴으로 업데이트")
        
        # 적응형 추출
        soup = BeautifulSoup(html, 'html.parser')
        adaptive_extractor = create_adaptive_crawler('news', validator)
        posts = adaptive_extractor(soup)
        
        logger.info(f"총 {len(posts)}개의 뉴스 추출 완료")
        
        # 추가 정보 보강
        for post in posts[:10]:  # 최신 10개만
            if not post.get('date'):
                post['date'] = datetime.now().strftime('%Y.%m.%d')
        
        return posts[:10]
        
    except Exception as e:
        logger.error(f"크롤링 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            driver.quit()

def send_news_to_discord(news_list):
    """디스코드로 뉴스 전송"""
    if not news_list:
        logger.info("전송할 뉴스가 없습니다.")
        return
    
    logger.info(f"{len(news_list)}개의 뉴스를 전송합니다.")
    
    # 메시지 생성
    content = "📰 **아이보스 마케팅 뉴스**\n"
    content += f"_{datetime.now().strftime('%Y년 %m월 %d일')} 업데이트_\n\n"
    
    for i, news in enumerate(news_list[:5], 1):
        content += f"**{i}. {news['title']}**\n"
        content += f"   📅 {news.get('date', '')}\n"
        content += f"   🔗 [자세히 보기]({news['link']})\n\n"
    
    if len(news_list) > 5:
        content += f"_... 외 {len(news_list)-5}개의 뉴스가 더 있습니다._\n\n"
    
    content += f"더 많은 뉴스는 [아이보스 뉴스 페이지](https://www.i-boss.co.kr/ab-7214)에서 확인하세요."
    
    # 웹훅 전송
    data = {
        "content": content,
        "username": "아이보스 뉴스봇 (적응형)"
    }
    
    try:
        response = requests.post(NEWS_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logger.info("디스코드 전송 성공")
        else:
            logger.error(f"디스코드 전송 실패: {response.status_code}")
    except Exception as e:
        logger.error(f"디스코드 전송 오류: {str(e)}")

def check_and_send_news():
    """새로운 뉴스 확인 및 전송"""
    import json
    
    # 기존 뉴스 ID 로드
    last_news_ids = []
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, 'r') as f:
            last_news_ids = json.load(f)
    
    # 새로운 뉴스 크롤링
    posts = get_news_adaptive()
    
    if not posts:
        logger.info("크롤링된 뉴스가 없습니다.")
        return
    
    # 새로운 뉴스만 필터링
    new_posts = []
    current_news_ids = []
    
    for post in posts:
        current_news_ids.append(post['id'])
        if post['id'] not in last_news_ids:
            new_posts.append(post)
    
    # 새로운 뉴스 전송
    if new_posts:
        send_news_to_discord(new_posts)
    else:
        logger.info("새로운 뉴스가 없습니다.")
        # 첫 실행이면 최신 3개만 전송
        if not last_news_ids and posts:
            send_news_to_discord(posts[:3])
    
    # 현재 뉴스 ID 저장
    with open(LAST_NEWS_FILE, 'w') as f:
        json.dump(current_news_ids[:10], f)

if __name__ == "__main__":
    try:
        logger.info("적응형 뉴스 크롤링 시작")
        check_and_send_news()
        logger.info("적응형 뉴스 크롤링 완료")
    except Exception as e:
        logger.error(f"크롤링 오류: {str(e)}")
        import traceback
        traceback.print_exc()