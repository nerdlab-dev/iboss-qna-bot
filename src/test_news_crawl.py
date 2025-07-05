#!/usr/bin/env python3
"""
아이보스 뉴스 크롤링 테스트 - 단순화 버전
"""

import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def test_news_crawl():
    print("=== 아이보스 뉴스 크롤링 테스트 ===")
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.i-boss.co.kr/ab-7214"
        print(f"URL 접속: {url}")
        driver.get(url)
        
        # 페이지 완전 로딩 대기
        print("페이지 로딩 대기 중...")
        time.sleep(10)
        
        # JavaScript로 스크롤하여 동적 로딩 트리거
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # 페이지 소스 확인
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print("\n=== 모든 링크 검색 ===")
        # 모든 링크 검색
        all_links = soup.find_all('a', href=True)
        news_count = 0
        
        for link in all_links:
            href = link.get('href', '')
            if 'ab-7214-' in href:
                news_count += 1
                title = link.text.strip()
                if title:
                    print(f"\n뉴스 {news_count}:")
                    print(f"제목: {title}")
                    print(f"링크: {href if href.startswith('http') else 'https://www.i-boss.co.kr' + href}")
        
        if news_count == 0:
            print("\n뉴스 링크를 찾을 수 없습니다.")
            
            # 디버그: 모든 div 확인
            print("\n=== div 태그 분석 ===")
            divs = soup.find_all('div', class_=True)
            for div in divs[:20]:  # 처음 20개만
                classes = ' '.join(div.get('class', []))
                if any(keyword in classes.lower() for keyword in ['news', 'article', 'list', 'item', 'content']):
                    print(f"클래스: {classes}")
                    text = div.text.strip()[:100]
                    if text:
                        print(f"내용: {text}...")
            
            # HTML 저장
            with open('news_test_debug.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("\n디버그 HTML이 news_test_debug.html에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_news_crawl()