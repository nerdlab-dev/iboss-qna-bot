#!/usr/bin/env python3
"""
링크 추출 테스트
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import re

def test_link_extraction():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.i-boss.co.kr/ab-2109"
        print(f"페이지 접속: {url}")
        driver.get(url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 다양한 선택자로 질문 찾기
        selectors = ['div.article', 'div[onclick*="viewDetail"]', 'tr[onclick*="viewDetail"]', 
                     'div[class*="article"]', 'li[onclick*="viewDetail"]']
        
        questions = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                print(f"선택자 '{selector}'로 {len(found)}개 요소 발견")
                questions = found[:5]  # 처음 5개만
                break
        
        print(f"\n총 {len(questions)}개 질문 분석")
        
        for idx, question in enumerate(questions, 1):
            print(f"\n=== 질문 {idx} ===")
            
            # onclick 속성 확인
            onclick = question.get('onclick', '')
            print(f"onclick: {onclick}")
            
            # 모든 a 태그 확인
            links = question.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.text.strip()[:50]
                print(f"링크: {href}")
                print(f"텍스트: {text}")
            
            # ID 추출 시도
            if onclick:
                match = re.search(r'viewDetail\([\'"](\d+)[\'"]', onclick)
                if match:
                    post_id = match.group(1)
                    print(f"추출된 ID: {post_id}")
                    print(f"생성된 링크: https://www.i-boss.co.kr/ab-2110-{post_id}")
            
            # 실제 상세 페이지 확인
            if onclick and 'viewDetail' in onclick:
                # JavaScript 실행해서 실제 URL 확인
                try:
                    driver.execute_script(onclick)
                    time.sleep(2)
                    new_url = driver.current_url
                    print(f"JavaScript 실행 후 URL: {new_url}")
                    driver.back()
                    time.sleep(1)
                except Exception as e:
                    print(f"JavaScript 실행 오류: {e}")
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_link_extraction()