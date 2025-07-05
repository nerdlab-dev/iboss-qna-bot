#!/usr/bin/env python3
"""
아이보스 뉴스 크롤링 - 로그인 버전
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 뉴스 웹훅 URL
NEWS_WEBHOOK_URL = "https://discord.com/api/webhooks/1391000157872590919/YGKb11bk4MCyIjJVh4fQzVHNOWAF50jPmnmsFD2xhtQffJ8AKnID5FgAwe0l32-MoD_3"

# 마지막 뉴스 저장 파일
LAST_NEWS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_news_login.json')

def load_last_news():
    """마지막 뉴스 ID 로드"""
    if os.path.exists(LAST_NEWS_FILE):
        with open(LAST_NEWS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_last_news(news_ids):
    """마지막 뉴스 ID 저장"""
    with open(LAST_NEWS_FILE, 'w') as f:
        json.dump(news_ids, f)

def get_chrome_driver():
    """Chrome 웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def login_to_iboss(driver):
    """아이보스 로그인"""
    try:
        logger.info("아이보스 로그인 시작")
        
        # 로그인 페이지 접속
        driver.get("https://www.i-boss.co.kr/ab-login")
        time.sleep(3)
        
        # 로그인 폼 찾기 - 다양한 선택자 시도
        wait = WebDriverWait(driver, 10)
        
        # 이메일 입력 - 다양한 선택자 시도
        email_selectors = [
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='user_id']"),
            (By.CSS_SELECTOR, "input[placeholder*='이메일']")
        ]
        
        email_input = None
        for by, selector in email_selectors:
            try:
                email_input = wait.until(EC.presence_of_element_located((by, selector)))
                logger.info(f"이메일 필드 발견: {selector}")
                break
            except:
                continue
        
        if not email_input:
            logger.error("이메일 입력 필드를 찾을 수 없습니다.")
            # 페이지 소스 저장
            with open('login_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            return False
        
        email_input.clear()
        email_input.send_keys("shane@rebeltech.info")
        
        # 비밀번호 입력 - 다양한 선택자 시도
        password_selectors = [
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='user_pw']")
        ]
        
        password_input = None
        for by, selector in password_selectors:
            try:
                password_input = driver.find_element(by, selector)
                logger.info(f"비밀번호 필드 발견: {selector}")
                break
            except:
                continue
        
        if password_input:
            password_input.clear()
            password_input.send_keys("project123!@")
        
        # 로그인 버튼 클릭 - 다양한 선택자 시도
        login_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CSS_SELECTOR, "button.login-btn"),
            (By.XPATH, "//button[contains(text(), '로그인')]"),
            (By.XPATH, "//input[@value='로그인']")
        ]
        
        for by, selector in login_selectors:
            try:
                login_button = driver.find_element(by, selector)
                logger.info(f"로그인 버튼 발견: {selector}")
                login_button.click()
                break
            except:
                continue
        
        # 로그인 완료 대기
        time.sleep(5)
        
        # 로그인 성공 확인
        current_url = driver.current_url
        logger.info(f"로그인 후 URL: {current_url}")
        
        if "ab-login" not in current_url or "mypage" in current_url:
            logger.info("로그인 성공")
            return True
        else:
            logger.error("로그인 실패")
            return False
            
    except Exception as e:
        logger.error(f"로그인 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_news_with_login():
    """로그인 후 뉴스 크롤링"""
    driver = None
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
        
        # 페이지 스크롤하여 더 많은 콘텐츠 로드
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        posts = []
        
        # 뉴스 기사 찾기 - 다양한 패턴 시도
        # 패턴 1: 직접 링크 (ab-2877- 패턴)
        news_links = soup.find_all('a', href=re.compile(r'ab-2877-\d+'))
        
        if news_links:
            logger.info(f"패턴 1로 {len(news_links)}개의 뉴스 발견")
            for link in news_links[:10]:
                title = link.text.strip()
                href = link.get('href', '')
                
                if title and len(title) > 5:
                    # URL 수정 - 앞에 슬래시가 없는 경우 추가
                    if not href.startswith('/') and not href.startswith('http'):
                        href = '/' + href
                    full_link = href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                    
                    # ID 추출
                    match = re.search(r'ab-2877-(\d+)', href)
                    post_id = match.group(1) if match else f"news_{len(posts)}"
                    
                    posts.append({
                        'id': post_id,
                        'title': title,
                        'link': full_link,
                        'date': datetime.now().strftime('%Y.%m.%d')
                    })
        
        # 패턴 2: onclick 이벤트가 있는 요소
        if not posts:
            logger.info("패턴 2: onclick 이벤트 확인")
            clickable_elements = soup.find_all(attrs={'onclick': True})
            
            for elem in clickable_elements:
                onclick = elem.get('onclick', '')
                if 'ab-2877-' in onclick or 'location.href' in onclick:
                    title = elem.get_text(strip=True)
                    
                    # URL 추출
                    match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                    if match and title and len(title) > 5:
                        href = match.group(1)
                        # URL 수정 - 앞에 슬래시가 없는 경우 추가
                        if not href.startswith('/') and not href.startswith('http'):
                            href = '/' + href
                        full_link = href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                        
                        # ID 추출
                        id_match = re.search(r'ab-2877-(\d+)', href)
                        post_id = id_match.group(1) if id_match else f"news_{len(posts)}"
                        
                        posts.append({
                            'id': post_id,
                            'title': title[:100],
                            'link': full_link,
                            'date': datetime.now().strftime('%Y.%m.%d')
                        })
        
        # 패턴 3: 리스트 아이템에서 찾기
        if not posts:
            logger.info("패턴 3: 리스트 아이템 확인")
            list_items = soup.find_all(['li', 'div'], class_=re.compile(r'item|article|news'))
            
            for item in list_items[:20]:
                link_elem = item.find('a', href=True)
                if link_elem:
                    title = link_elem.text.strip() or item.get_text(strip=True)[:100]
                    href = link_elem.get('href', '')
                    
                    if title and len(title) > 5 and 'ab-' in href:
                        # URL 수정 - 앞에 슬래시가 없는 경우 추가
                        if not href.startswith('/') and not href.startswith('http'):
                            href = '/' + href
                        full_link = href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                        
                        logger.debug(f"발견된 뉴스: {title[:50]}... -> {full_link}")
                        
                        posts.append({
                            'id': f"news_{len(posts)}_{datetime.now().strftime('%H%M')}",
                            'title': title,
                            'link': full_link,
                            'date': datetime.now().strftime('%Y.%m.%d')
                        })
        
        logger.info(f"총 {len(posts)}개의 뉴스 수집")
        
        # 디버그: HTML 저장
        if not posts:
            with open('news_login_debug.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("디버그 HTML 저장: news_login_debug.html")
        
        return posts[:10]  # 최신 10개만
        
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
        "username": "아이보스 뉴스봇"
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
    # 기존 뉴스 ID 로드
    last_news_ids = load_last_news()
    
    # 새로운 뉴스 크롤링
    posts = get_news_with_login()
    
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
    save_last_news(current_news_ids[:10])

if __name__ == "__main__":
    check_and_send_news()