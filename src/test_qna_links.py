#!/usr/bin/env python3
"""
질문답변 링크 추출 테스트 - 실제 봇과 동일한 방식 사용
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.iboss_qna_bot import get_chrome_driver
from bs4 import BeautifulSoup
import time
import re

def test_qna_links():
    driver = None
    try:
        driver = get_chrome_driver()
        url = "https://www.i-boss.co.kr/ab-2109"
        print(f"페이지 접속: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(5)
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 질문 목록 찾기
        questions = soup.select('div.article')
        print(f"\n총 {len(questions)}개의 질문 발견")
        
        # 처음 3개만 상세 분석
        for idx, question in enumerate(questions[:3], 1):
            print(f"\n{'='*50}")
            print(f"질문 {idx} 분석")
            print('='*50)
            
            # HTML 구조 출력
            print("\nHTML 구조:")
            print(str(question)[:200] + "...")
            
            # onclick 속성 확인
            onclick = question.get('onclick', '')
            if onclick:
                print(f"\nonclick 속성: {onclick}")
                
                # viewDetail 함수에서 ID 추출
                match = re.search(r'viewDetail\([\'"](\d+)[\'"]', onclick)
                if match:
                    post_id = match.group(1)
                    print(f"추출된 게시물 ID: {post_id}")
                    print(f"생성된 상세 페이지 링크: https://www.i-boss.co.kr/ab-2110-{post_id}")
            
            # 제목 추출
            title_elem = question.select_one('div.content a')
            if title_elem:
                title = title_elem.text.strip()
                href = title_elem.get('href', '')
                print(f"\n제목: {title}")
                print(f"기존 href: {href}")
        
        # 실제 상세 페이지 접속 테스트
        if questions:
            first_question = questions[0]
            onclick = first_question.get('onclick', '')
            if onclick and 'viewDetail' in onclick:
                match = re.search(r'viewDetail\([\'"](\d+)[\'"]', onclick)
                if match:
                    post_id = match.group(1)
                    detail_url = f"https://www.i-boss.co.kr/ab-2110-{post_id}"
                    
                    print(f"\n\n실제 상세 페이지 접속 테스트:")
                    print(f"URL: {detail_url}")
                    driver.get(detail_url)
                    time.sleep(3)
                    
                    print(f"접속 후 URL: {driver.current_url}")
                    print(f"페이지 제목: {driver.title}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_qna_links()