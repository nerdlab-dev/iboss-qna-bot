#!/usr/bin/env python3
"""
아이보스 뉴스 페이지 구조 분석 - Selenium 사용
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re

def analyze_news_structure():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 뉴스 페이지 접속
        url = "https://www.i-boss.co.kr/ab-7214"
        print(f"뉴스 페이지 접속: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        print("페이지 로딩 대기...")
        time.sleep(5)
        
        # 스크롤하여 더 많은 콘텐츠 로드
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        print("\n=== 뉴스 링크 패턴 분석 ===")
        
        # 모든 링크 확인
        all_links = soup.find_all('a', href=True)
        news_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.text.strip()
            
            # 뉴스 관련 링크 패턴 찾기
            if any(pattern in href for pattern in ['ab-6869-', 'ab-news-', 'article', '/news/']):
                if text and len(text) > 10:
                    news_links.append({
                        'href': href,
                        'text': text[:100],
                        'full_link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                    })
        
        print(f"\n발견된 뉴스 링크: {len(news_links)}개")
        
        # 처음 5개 출력
        for i, link in enumerate(news_links[:5], 1):
            print(f"\n뉴스 {i}:")
            print(f"제목: {link['text']}")
            print(f"링크: {link['full_link']}")
        
        # onclick 이벤트가 있는 요소 찾기
        print("\n\n=== onclick 이벤트 분석 ===")
        onclick_elements = soup.find_all(attrs={'onclick': True})
        
        news_onclick = []
        for elem in onclick_elements:
            onclick = elem.get('onclick', '')
            if any(keyword in onclick for keyword in ['viewDetail', 'location.href', 'window.open']):
                text = elem.get_text(strip=True)[:100]
                if text and len(text) > 10:
                    news_onclick.append({
                        'onclick': onclick,
                        'text': text,
                        'tag': elem.name
                    })
        
        print(f"\n발견된 onclick 이벤트: {len(news_onclick)}개")
        
        for i, item in enumerate(news_onclick[:5], 1):
            print(f"\n이벤트 {i}:")
            print(f"태그: {item['tag']}")
            print(f"onclick: {item['onclick']}")
            print(f"텍스트: {item['text']}")
            
            # onclick에서 링크 추출 시도
            # location.href='URL' 패턴
            match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", item['onclick'])
            if match:
                extracted_url = match.group(1)
                print(f"추출된 URL: {extracted_url}")
        
        # 실제 뉴스 기사 하나 접속해보기
        if news_links:
            test_url = news_links[0]['full_link']
            print(f"\n\n=== 뉴스 상세 페이지 테스트 ===")
            print(f"접속 URL: {test_url}")
            driver.get(test_url)
            time.sleep(3)
            print(f"접속 후 URL: {driver.current_url}")
            print(f"페이지 제목: {driver.title}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_news_structure()