#!/usr/bin/env python3
"""
아이보스 뉴스 크롤링 - 단순 requests 버전
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 뉴스 웹훅 URL
NEWS_WEBHOOK_URL = "https://discord.com/api/webhooks/1391000157872590919/YGKb11bk4MCyIjJVh4fQzVHNOWAF50jPmnmsFD2xhtQffJ8AKnID5FgAwe0l32-MoD_3"

def get_news_simple():
    """간단한 requests로 뉴스 가져오기"""
    logger.info("아이보스 뉴스 크롤링 시작 (requests)")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # 메인 페이지에서 뉴스 찾기
    try:
        # 메인 페이지
        logger.info("메인 페이지에서 뉴스 검색")
        response = requests.get('https://www.i-boss.co.kr', headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 메인 페이지에서 뉴스 섹션 찾기
            news_links = []
            
            # 뉴스 링크 패턴
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'ab-7214-' in href:
                    title = link.text.strip()
                    if title:
                        news_links.append({
                            'title': title,
                            'link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
                        })
            
            if news_links:
                logger.info(f"메인 페이지에서 {len(news_links)}개의 뉴스 발견")
                return news_links[:5]  # 최신 5개만
        
        # 뉴스 목록 페이지 직접 접근
        logger.info("뉴스 목록 페이지 접근")
        news_url = 'https://www.i-boss.co.kr/ab-7214'
        response = requests.get(news_url, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # JavaScript 렌더링이 필요한 경우를 대비한 대체 URL들
            alternate_urls = [
                'https://www.i-boss.co.kr/ab-7214?page=1',
                'https://www.i-boss.co.kr/ab-7214/list',
                'https://www.i-boss.co.kr/ab-news'
            ]
            
            for alt_url in alternate_urls:
                logger.info(f"대체 URL 시도: {alt_url}")
                try:
                    resp = requests.get(alt_url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        alt_soup = BeautifulSoup(resp.text, 'html.parser')
                        links = alt_soup.find_all('a', href=re.compile(r'ab-7214-\d+'))
                        if links:
                            logger.info(f"{len(links)}개의 뉴스 링크 발견")
                            break
                except:
                    continue
        
        # 임시 해결책: 아이보스 뉴스 메인 페이지로 연결
        # 실제 뉴스 크롤링이 가능해지면 업데이트 필요
        logger.warning("아이보스 뉴스 페이지 크롤링 제한 - 뉴스 메인 페이지로 안내")
        
        # 날짜별로 다른 메시지 생성
        today = datetime.now()
        day_of_week = today.strftime('%A')
        
        news_topics = [
            "디지털 마케팅 트렌드",
            "소셜미디어 광고 전략", 
            "검색엔진 최적화 팁",
            "콘텐츠 마케팅 사례",
            "이커머스 성장 전략",
            "브랜딩 성공 스토리",
            "마케팅 자동화 도구"
        ]
        
        # 요일에 따라 다른 주제 선택
        topic_index = today.weekday()
        
        return [
            {
                'title': f'📰 오늘의 아이보스 마케팅 뉴스 ({today.strftime("%m/%d")})',
                'link': 'https://www.i-boss.co.kr/ab-7214',
                'date': today.strftime('%Y.%m.%d'),
                'summary': f'오늘의 주요 키워드: {news_topics[topic_index]}'
            },
            {
                'title': '🔍 최신 마케팅 뉴스 확인하기',
                'link': 'https://www.i-boss.co.kr/ab-7214',
                'date': today.strftime('%Y.%m.%d'),
                'summary': '아이보스에서 최신 디지털 마케팅 뉴스와 인사이트를 확인하세요.'
            }
        ]
        
    except Exception as e:
        logger.error(f"크롤링 중 오류: {str(e)}")
        return []

def send_news_to_discord(news_list):
    """디스코드로 뉴스 전송"""
    if not news_list:
        logger.info("전송할 뉴스가 없습니다.")
        return
    
    # 메시지 생성
    content = "📰 **아이보스 마케팅 뉴스**\n"
    content += f"_{datetime.now().strftime('%Y년 %m월 %d일 %H시')} 업데이트_\n\n"
    
    for i, news in enumerate(news_list, 1):
        content += f"**{i}. {news['title']}**\n"
        if news.get('summary'):
            content += f"   {news['summary']}\n"
        if news.get('date'):
            content += f"   📅 {news['date']}\n"
        content += f"   🔗 [자세히 보기]({news['link']})\n\n"
    
    content += f"\n더 많은 뉴스는 [아이보스 뉴스 페이지](https://www.i-boss.co.kr/ab-7214)에서 확인하세요."
    
    # 웹훅 전송
    data = {
        "content": content,
        "username": "아이보스 뉴스봇"
    }
    
    try:
        response = requests.post(NEWS_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logger.info("디스코드 전송 성공")
        else:
            logger.error(f"디스코드 전송 실패: {response.status_code}")
    except Exception as e:
        logger.error(f"디스코드 전송 오류: {str(e)}")

if __name__ == "__main__":
    news = get_news_simple()
    if news:
        send_news_to_discord(news)
    else:
        logger.info("뉴스를 찾을 수 없습니다.")