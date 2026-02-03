#!/usr/bin/env python3
"""
Q&A 링크 디버그 - 실제 링크 구조 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

def debug_qna_links():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.i-boss.co.kr/ab-2109"
        print(f"Q&A 페이지 접속: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(5)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # HTML 저장
        with open('qna_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("디버그 HTML 저장: qna_page_debug.html")
        
        print("\n=== Q&A 링크 분석 ===")
        
        # 다양한 셀렉터로 질문 목록 찾기
        selectors = ['div.article', 'div.item', 'li.item', 'div.question', 'div.qna-item']
        questions = []
        
        for selector in selectors:
            questions = soup.select(selector)
            if questions:
                print(f"셀렉터 '{selector}'로 {len(questions)}개의 질문 발견")
                break
        
        if not questions:
            # 모든 div에서 onclick이 있는 것 찾기
            questions = soup.find_all('div', onclick=True)
            print(f"onclick이 있는 div: {len(questions)}개")
            
            # viewDetail 함수가 있는 것만 필터링
            questions = [q for q in questions if 'viewDetail' in q.get('onclick', '')]
            print(f"viewDetail이 있는 div: {len(questions)}개")
        
        for idx, question in enumerate(questions[:5], 1):
            print(f"\n질문 {idx}:")
            
            # onclick 속성 확인
            onclick = question.get('onclick', '')
            if onclick:
                print(f"onclick: {onclick}")
                # viewDetail('30173') 형식에서 ID 추출
                match = re.search(r'viewDetail\([\'"](\d+)[\'"]', onclick)
                if match:
                    post_id = match.group(1)
                    print(f"추출된 ID: {post_id}")
                    print(f"예상 링크: https://www.i-boss.co.kr/ab-2110-{post_id}")
            
            # a 태그 링크 확인
            links = question.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.text.strip()[:50]
                if text:
                    print(f"링크 텍스트: {text}")
                    print(f"href: {href}")
                    
                    # 실제 URL 구성
                    if not href.startswith('http'):
                        full_url = f"https://www.i-boss.co.kr{href}"
                    else:
                        full_url = href
                    print(f"전체 URL: {full_url}")
        
        # 첫 번째 질문 클릭 테스트
        print("\n\n=== 첫 번째 질문 클릭 테스트 ===")
        if questions:
            first_question = questions[0]
            onclick = first_question.get('onclick', '')
            if onclick:
                print(f"onclick 실행: {onclick}")
                # JavaScript 실행
                driver.execute_script(onclick)
                time.sleep(3)
                
                print(f"클릭 후 URL: {driver.current_url}")
                print(f"페이지 제목: {driver.title}")
                
                # 상세 페이지 내용 확인
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                title_elem = detail_soup.select_one('h1, h2, .title')
                if title_elem:
                    print(f"상세 페이지 제목: {title_elem.text.strip()}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_qna_links()