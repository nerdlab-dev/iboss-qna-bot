#!/usr/bin/env python3
"""
뉴스 링크 디버그 - 로그인 후 실제 링크 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.iboss_news_login import get_chrome_driver, login_to_iboss
from bs4 import BeautifulSoup
import time
import re

def debug_news_links():
    driver = None
    try:
        driver = get_chrome_driver()
        
        # 로그인
        if not login_to_iboss(driver):
            print("로그인 실패")
            return
        
        # 뉴스 페이지 접속
        print("\n뉴스 페이지 접속 중...")
        driver.get("https://www.i-boss.co.kr/ab-7214")
        time.sleep(5)
        
        # 페이지 스크롤
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        print("\n=== 모든 링크 분석 ===")
        
        # 모든 a 태그 찾기
        all_links = soup.find_all('a', href=True)
        news_links = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.text.strip()
            
            # 뉴스 관련 링크 필터링
            if text and len(text) > 10 and 'ab-' in href:
                news_links.append({
                    'text': text,
                    'href': href,
                    'full_url': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                })
        
        print(f"\n총 {len(news_links)}개의 뉴스 링크 발견")
        
        # 처음 10개 출력
        for i, news in enumerate(news_links[:10], 1):
            print(f"\n뉴스 {i}:")
            print(f"제목: {news['text'][:80]}...")
            print(f"원본 href: {news['href']}")
            print(f"전체 URL: {news['full_url']}")
            
            # 링크 패턴 분석
            if 'ab-6869-' in news['href']:
                print("→ 개별 뉴스 기사 링크 (ab-6869-)")
            elif 'ab-7214' in news['href'] and not re.search(r'ab-7214-\d+', news['href']):
                print("→ 뉴스 목록 페이지 링크")
            elif re.search(r'ab-\d+-\d+', news['href']):
                print("→ 개별 콘텐츠 링크")
        
        # 실제 뉴스 페이지 하나 접속 테스트
        if news_links:
            print("\n\n=== 첫 번째 뉴스 상세 페이지 테스트 ===")
            test_news = news_links[0]
            print(f"접속할 뉴스: {test_news['text'][:50]}...")
            print(f"URL: {test_news['full_url']}")
            
            driver.get(test_news['full_url'])
            time.sleep(3)
            
            print(f"\n접속 후 실제 URL: {driver.current_url}")
            print(f"페이지 제목: {driver.title}")
            
            # URL이 변경되었는지 확인
            if driver.current_url != test_news['full_url']:
                print("⚠️ URL이 리다이렉트되었습니다!")
        
        # HTML 저장
        with open('news_links_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\n\n디버그 HTML 저장: news_links_debug.html")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_news_links()