#!/usr/bin/env python3
"""
아이보스 메인 페이지에서 뉴스 찾기
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re

def find_news_from_main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 메인 페이지 접속
        url = "https://www.i-boss.co.kr"
        print(f"메인 페이지 접속: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        print("\n=== 메인 페이지에서 뉴스 섹션 찾기 ===")
        
        # 뉴스 관련 섹션 찾기
        news_sections = soup.find_all(['div', 'section'], class_=re.compile(r'news|article|content', re.I))
        print(f"뉴스 관련 섹션: {len(news_sections)}개")
        
        # 모든 링크에서 뉴스 찾기
        all_links = soup.find_all('a', href=True)
        news_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.text.strip()
            
            # 뉴스 관련 링크 패턴
            if 'ab-6869-' in href and text and len(text) > 10:
                news_links.append({
                    'title': text,
                    'href': href,
                    'full_link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                })
        
        print(f"\n발견된 뉴스 링크 (ab-6869-): {len(news_links)}개")
        
        # 처음 5개 출력
        for i, news in enumerate(news_links[:5], 1):
            print(f"\n뉴스 {i}:")
            print(f"제목: {news['title']}")
            print(f"링크: {news['full_link']}")
            
            # ID 추출
            match = re.search(r'ab-6869-(\d+)', news['href'])
            if match:
                news_id = match.group(1)
                print(f"뉴스 ID: {news_id}")
        
        # 뉴스 카테고리 링크 찾기
        print("\n\n=== 뉴스 카테고리 링크 찾기 ===")
        category_keywords = ['뉴스', 'news', '기사', 'article', '콘텐츠', 'content']
        
        for link in all_links:
            text = link.text.strip().lower()
            href = link.get('href', '')
            
            if any(keyword in text for keyword in category_keywords) and 'ab-' in href:
                print(f"카테고리: {link.text.strip()}")
                print(f"링크: {href}")
        
        # 실제 뉴스 기사 접속 테스트
        if news_links:
            test_news = news_links[0]
            print(f"\n\n=== 뉴스 상세 페이지 테스트 ===")
            print(f"접속할 뉴스: {test_news['title']}")
            print(f"URL: {test_news['full_link']}")
            
            driver.get(test_news['full_link'])
            time.sleep(3)
            
            print(f"접속 후 URL: {driver.current_url}")
            print(f"페이지 제목: {driver.title}")
            
            # 콘텐츠 확인
            content_soup = BeautifulSoup(driver.page_source, 'html.parser')
            article_content = content_soup.find(['div', 'article'], class_=re.compile(r'content|article|body', re.I))
            
            if article_content:
                print("\n기사 내용 일부:")
                print(article_content.text.strip()[:200] + "...")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    find_news_from_main()