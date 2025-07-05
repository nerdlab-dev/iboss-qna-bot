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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 뉴스 웹훅 URL
NEWS_WEBHOOK_URL = "https://discord.com/api/webhooks/1391000157872590919/YGKb11bk4MCyIjJVh4fQzVHNOWAF50jPmnmsFD2xhtQffJ8AKnID5FgAwe0l32-MoD_3"

# 마지막으로 확인한 뉴스 ID를 저장할 파일
LAST_NEWS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_news.json')

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
    # JavaScript 활성화
    chrome_options.add_argument("--enable-javascript")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_news_from_main_page():
    """메인 페이지에서 뉴스 수집"""
    logger.info("아이보스 메인 페이지에서 뉴스 수집 시작")
    
    driver = None
    try:
        driver = get_chrome_driver()
        # 먼저 메인 페이지 접속
        url = "https://www.i-boss.co.kr"
        logger.info(f"메인 페이지 접속: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 뉴스 섹션으로 이동
        news_url = "https://www.i-boss.co.kr/ab-7214"
        logger.info(f"뉴스 페이지 접속: {news_url}")
        driver.get(news_url)
        
        # 페이지 완전 로딩 대기
        time.sleep(5)
        
        # JavaScript 실행하여 동적 콘텐츠 로드
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        posts = []
        
        # 여러 가지 선택자로 뉴스 찾기
        selectors = [
            'a[href*="ab-7214-"]',
            'div.news_list a',
            'div.article_list a',
            'div.content_list a',
            'ul.news_list li a',
            'div[class*="news"] a',
            'div[class*="article"] a'
        ]
        
        news_elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"선택자 '{selector}'로 {len(elements)}개의 요소 발견")
                for elem in elements:
                    href = elem.get('href', '')
                    if 'ab-7214-' in href and elem.text.strip():
                        news_elements.append(elem)
        
        # 중복 제거
        seen_urls = set()
        unique_news = []
        for elem in news_elements:
            href = elem.get('href', '')
            if href not in seen_urls:
                seen_urls.add(href)
                unique_news.append(elem)
        
        logger.info(f"총 {len(unique_news)}개의 고유 뉴스 발견")
        
        for idx, elem in enumerate(unique_news[:10], 1):  # 최신 10개만
            try:
                title = elem.text.strip()
                link = elem.get('href', '')
                
                if not link.startswith('http'):
                    link = f"https://www.i-boss.co.kr{link}"
                
                # ID 추출
                match = re.search(r'ab-7214-(\d+)', link)
                post_id = match.group(1) if match else f"news_{idx}"
                
                # 부모 요소에서 추가 정보 찾기
                parent = elem.parent
                date = ""
                summary = ""
                
                if parent:
                    # 날짜 찾기
                    date_elem = parent.find(text=re.compile(r'\d{4}[.-]\d{2}[.-]\d{2}'))
                    if date_elem:
                        date = date_elem.strip()
                    
                    # 요약 찾기
                    summary_elem = parent.find('p')
                    if summary_elem and summary_elem != elem:
                        summary = summary_elem.text.strip()[:200]
                
                post_data = {
                    'id': post_id,
                    'title': title,
                    'link': link,
                    'date': date,
                    'summary': summary
                }
                posts.append(post_data)
                logger.debug(f"뉴스 {idx}: {title}")
                
            except Exception as e:
                logger.error(f"뉴스 {idx} 처리 중 오류: {str(e)}")
                continue
        
        return posts
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

def send_news_webhook(posts):
    """디스코드 웹훅으로 뉴스 전송"""
    if not posts:
        logger.info("전송할 새로운 뉴스가 없습니다.")
        return
    
    logger.info(f"{len(posts)}개의 새로운 뉴스를 전송합니다.")
    
    # 메시지 생성
    content = "📰 **아이보스 마케팅 뉴스**\n"
    content += f"_{datetime.now().strftime('%Y년 %m월 %d일')} 새로운 뉴스 {len(posts)}건_\n\n"
    
    for i, post in enumerate(posts[:5], 1):
        content += f"**{i}. {post['title']}**\n"
        if post.get('summary'):
            content += f"└ {post['summary'][:100]}...\n"
        if post.get('date'):
            content += f"└ 📅 {post['date']}\n"
        content += f"└ [자세히 보기]({post['link']})\n\n"
    
    if len(posts) > 5:
        content += f"_... 외 {len(posts)-5}개의 뉴스가 더 있습니다._\n"
    
    content += f"\n🔗 [아이보스 뉴스 전체보기](https://www.i-boss.co.kr/ab-7214)"
    
    # 웹훅 전송
    data = {
        "content": content,
        "username": "아이보스 뉴스봇",
        "avatar_url": "https://www.i-boss.co.kr/favicon.ico"
    }
    
    try:
        response = requests.post(NEWS_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logger.info("디스코드 메시지 전송 완료")
        else:
            logger.error(f"디스코드 메시지 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"디스코드 메시지 전송 중 오류: {str(e)}")

def check_and_send_news():
    """새로운 뉴스 확인 및 전송"""
    # 기존 뉴스 ID 로드
    last_news_ids = load_last_news()
    
    # 새로운 뉴스 크롤링
    posts = get_news_from_main_page()
    
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
    
    # 첫 실행이거나 새로운 뉴스가 있을 때
    if not last_news_ids:
        logger.info("첫 실행입니다. 최신 뉴스를 전송합니다.")
        send_news_webhook(posts[:3])  # 첫 실행시 최신 3개만
    elif new_posts:
        send_news_webhook(new_posts)
    else:
        logger.info("새로운 뉴스가 없습니다.")
    
    # 현재 뉴스 ID 저장
    save_last_news(current_news_ids[:10])

if __name__ == "__main__":
    check_and_send_news()