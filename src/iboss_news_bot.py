import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
from datetime import datetime, time as dt_time, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 뉴스 웹훅 URL
NEWS_WEBHOOK_URL = "https://discord.com/api/webhooks/1391000157872590919/YGKb11bk4MCyIjJVh4fQzVHNOWAF50jPmnmsFD2xhtQffJ8AKnID5FgAwe0l32-MoD_3"

# 마지막으로 확인한 뉴스 ID를 저장할 파일
LAST_NEWS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_news_posts.json')

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

def get_news_posts():
    """아이보스 뉴스 크롤링"""
    logger.info("아이보스 뉴스 크롤링 시작")
    url = "https://www.i-boss.co.kr/ab-7214"
    
    driver = None
    try:
        driver = get_chrome_driver()
        logger.info(f"URL 접속: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 20)
        try:
            # 뉴스 컨텐츠가 로드될 때까지 대기
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='ab-7214-']")))
            time.sleep(3)  # 추가 로딩 대기
        except:
            logger.warning("페이지 로딩 타임아웃")
            time.sleep(5)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        posts = []
        # 뉴스 목록 찾기 - 다양한 선택자 시도
        selectors = [
            'div.list_item',
            'div.news_item',
            'article',
            'div.article',
            'li.news',
            'div.row'
        ]
        
        articles = []
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                logger.info(f"선택자 '{selector}'로 {len(articles)}개의 기사 발견")
                break
        
        if not articles:
            # 모든 링크를 찾아서 뉴스 패턴 확인
            all_links = soup.find_all('a', href=True)
            news_links = []
            for link in all_links:
                href = link.get('href', '')
                if 'ab-7214-' in href and link.text.strip():
                    news_links.append(link)
            
            if news_links:
                logger.info(f"링크 패턴으로 {len(news_links)}개의 뉴스 발견")
                # 링크를 article로 변환
                articles = []
                for link in news_links[:10]:  # 최신 10개만
                    parent = link.parent
                    if parent:
                        articles.append(parent)
            else:
                logger.warning("뉴스를 찾을 수 없습니다.")
                # 디버그용 HTML 저장
                with open('news_debug.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info("디버그용 HTML이 news_debug.html에 저장되었습니다.")
                return []
        
        logger.info(f"총 {len(articles)}개의 뉴스 발견")
        
        for idx, article in enumerate(articles[:10], 1):  # 최신 10개만
            try:
                # article이 링크 요소인 경우
                if article.name == 'a':
                    title = article.text.strip()
                    link = article.get('href', '')
                else:
                    # 제목과 링크 찾기
                    title_element = article.find('a')
                    if not title_element:
                        continue
                    
                    title = title_element.text.strip()
                    link = title_element.get('href', '')
                
                if not title:
                    continue
                    
                if link and not link.startswith('http'):
                    link = f"https://www.i-boss.co.kr{link}"
                
                # 날짜 정보
                date_element = article.select_one('span.date, div.date, p.date')
                date = date_element.text.strip() if date_element else ''
                
                # 카테고리
                category_element = article.select_one('span.category, div.category')
                category = category_element.text.strip() if category_element else ''
                
                # 요약
                summary_element = article.select_one('p.summary, div.summary, div.content')
                summary = ''
                if summary_element:
                    summary = summary_element.text.strip()[:200]
                
                # 게시물 ID 추출
                post_id = ''
                # 링크에서 ID 추출 시도
                if link:
                    match = re.search(r'ab-7214-(\d+)', link)
                    if match:
                        post_id = match.group(1)
                
                if not post_id:
                    post_id = f"news_{idx}_{datetime.now().strftime('%Y%m%d%H%M')}"
                
                post_data = {
                    'id': post_id,
                    'title': title,
                    'link': link,
                    'date': date,
                    'category': category,
                    'summary': summary
                }
                posts.append(post_data)
                logger.debug(f"뉴스 {idx} 처리 완료: {title}")
                
            except Exception as e:
                logger.error(f"뉴스 {idx} 처리 중 오류: {str(e)}")
                continue
        
        logger.info(f"총 {len(posts)}개의 뉴스 수집 완료")
        return posts
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

def send_news_to_discord(posts):
    """디스코드 웹훅으로 뉴스 전송"""
    if not posts:
        logger.info("전송할 새로운 뉴스가 없습니다.")
        return
    
    logger.info(f"{len(posts)}개의 새로운 뉴스를 전송합니다.")
    
    # 임베드 생성
    embeds = []
    
    # 메인 임베드
    main_embed = {
        "title": "📰 아이보스 마케팅 뉴스",
        "description": f"{len(posts)}개의 새로운 뉴스가 있습니다.",
        "color": 16711680,  # 빨간색
        "timestamp": datetime.now().isoformat(),
        "fields": []
    }
    
    for i, post in enumerate(posts[:5]):  # 최대 5개까지
        field_value = ""
        if post.get('summary'):
            field_value += f"{post['summary'][:100]}...\n"
        if post.get('category'):
            field_value += f"📁 {post['category']} "
        if post.get('date'):
            field_value += f"| 📅 {post['date']}"
        if field_value:
            field_value += "\n"
        field_value += f"[자세히 보기]({post['link']})"
        
        # 제목이 너무 길면 자르기
        title = post['title']
        if len(title) > 250:
            title = title[:247] + "..."
        
        main_embed["fields"].append({
            "name": f"{i+1}. {title}",
            "value": field_value,
            "inline": False
        })
    
    if len(posts) > 5:
        main_embed["fields"].append({
            "name": "추가 뉴스",
            "value": f"외 {len(posts)-5}개의 뉴스가 더 있습니다.",
            "inline": False
        })
    
    main_embed["footer"] = {
        "text": "아이보스 마케팅 뉴스",
        "icon_url": "https://www.i-boss.co.kr/favicon.ico"
    }
    
    embeds.append(main_embed)
    
    # 웹훅 전송
    data = {
        "embeds": embeds
    }
    
    try:
        response = requests.post(NEWS_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logger.info("디스코드 메시지 전송 완료")
        else:
            logger.error(f"디스코드 메시지 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"디스코드 메시지 전송 중 오류: {str(e)}")

def check_new_news():
    """새로운 뉴스 확인 및 알림"""
    # 기존 뉴스 ID 로드
    last_news_ids = load_last_news()
    
    # 새로운 뉴스 크롤링
    posts = get_news_posts()
    
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
    
    # 현재 뉴스 ID 저장
    save_last_news(current_news_ids[:10])  # 최신 10개만 저장

if __name__ == "__main__":
    # 직접 실행시 즉시 크롤링
    check_new_news()