#!/usr/bin/env python3
"""
아이보스 뉴스 페이지 구조 분석
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

def analyze_news_page():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("페이지 접속 중...")
        driver.get("https://www.i-boss.co.kr/ab-7214")
        
        # 충분한 로딩 시간
        print("로딩 대기 중...")
        time.sleep(10)
        
        # 스크롤하여 더 많은 콘텐츠 로드
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        # iframe 확인
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\niframe 개수: {len(iframes)}")
        
        # 현재 URL 확인
        print(f"현재 URL: {driver.current_url}")
        
        # 페이지 소스 분석
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 모든 링크 분석
        print("\n=== 뉴스 관련 링크 분석 ===")
        all_links = soup.find_all('a', href=True)
        news_count = 0
        
        for link in all_links:
            href = link.get('href', '')
            text = link.text.strip()
            
            # 뉴스 링크 패턴 확인
            if any(pattern in href for pattern in ['ab-7214-', 'news', 'article', 'content']):
                if text and len(text) > 10:  # 제목이 있는 링크만
                    news_count += 1
                    print(f"\n뉴스 {news_count}:")
                    print(f"제목: {text[:50]}...")
                    print(f"링크: {href}")
                    
                    # 부모 요소 정보
                    parent = link.parent
                    if parent:
                        parent_class = ' '.join(parent.get('class', []))
                        print(f"부모 클래스: {parent_class}")
        
        if news_count == 0:
            print("\n뉴스 링크를 찾을 수 없습니다.")
            
            # 텍스트 내용으로 뉴스 찾기
            print("\n=== 텍스트 패턴으로 뉴스 찾기 ===")
            # 뉴스 제목 패턴 (한글 제목)
            import re
            korean_titles = soup.find_all(text=re.compile(r'[가-힣]{5,}'))
            
            for idx, text in enumerate(korean_titles[:20]):
                text = text.strip()
                if len(text) > 20 and len(text) < 100:
                    parent = text.parent
                    if parent and parent.name == 'a':
                        href = parent.get('href', '')
                        if href:
                            print(f"\n텍스트 기반 발견:")
                            print(f"제목: {text}")
                            print(f"링크: {href}")
        
        # HTML 저장
        with open('news_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\n\n전체 HTML이 news_page_debug.html에 저장되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_news_page()