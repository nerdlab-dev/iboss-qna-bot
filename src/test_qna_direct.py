#!/usr/bin/env python3
"""
Q&A 봇 직접 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.iboss_qna_bot import get_qna_posts

# Q&A 게시물 가져오기
print("Q&A 크롤링 시작...")
posts = get_qna_posts()

if posts:
    print(f"\n총 {len(posts)}개의 Q&A 발견")
    
    # 처음 5개 출력
    for i, post in enumerate(posts[:5], 1):
        print(f"\n{'='*60}")
        print(f"질문 {i}:")
        print(f"ID: {post['id']}")
        print(f"제목: {post['title']}")
        print(f"링크: {post['link']}")
        print(f"작성자: {post.get('author', 'N/A')}")
        print(f"날짜: {post.get('date', 'N/A')}")
        print(f"내용: {post.get('content', 'N/A')[:100]}...")
        
        # 링크 패턴 확인
        if 'ab-2110-' in post['link']:
            print("✅ 개별 Q&A 페이지 링크")
        elif 'ab-2109' in post['link']:
            print("⚠️ 목록 페이지 링크")
        else:
            print("❓ 알 수 없는 링크 형식")
else:
    print("Q&A를 찾을 수 없습니다.")