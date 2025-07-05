#!/usr/bin/env python3
"""
아이보스 크롤링 테스트 스크립트
봇 없이 크롤링 기능만 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.iboss_qna_bot import get_qna_posts
import json
from datetime import datetime

def test_crawling():
    print("="*50)
    print("아이보스 질문답변 크롤링 테스트")
    print(f"실행 시간: {datetime.now()}")
    print("="*50)
    
    # 크롤링 실행
    posts = get_qna_posts()
    
    if not posts:
        print("\n❌ 크롤링 실패 또는 게시물이 없습니다.")
        return
    
    print(f"\n✅ 크롤링 성공! 총 {len(posts)}개의 질문을 찾았습니다.\n")
    
    # 결과 출력
    for i, post in enumerate(posts[:5], 1):
        print(f"--- 질문 {i} ---")
        print(f"제목: {post['title']}")
        print(f"링크: {post['link']}")
        print(f"작성자: {post.get('author', 'N/A')}")
        print(f"날짜: {post.get('date', 'N/A')}")
        if post.get('content'):
            print(f"내용: {post['content'][:100]}...")
        if post.get('tags'):
            print(f"태그: {', '.join(post['tags'])}")
        print(f"ID: {post['id']}")
        print()
    
    # JSON 파일로 저장
    output_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"전체 결과가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    test_crawling()