#!/usr/bin/env python3
"""
아이보스 통합 크롤링 봇
매일 오전 8시에 질문답변과 뉴스를 크롤링하여 디스코드로 전송
"""

import asyncio
import logging
from datetime import datetime

# 각 봇 모듈 임포트
from iboss_qna_bot import check_new_qna
from iboss_news_simple import get_news_simple, send_news_to_discord

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_daily_crawling():
    """매일 실행할 크롤링 작업"""
    logger.info("=== 아이보스 일일 크롤링 시작 ===")
    logger.info(f"실행 시간: {datetime.now()}")
    
    try:
        # 1. 질문답변 크롤링 (비동기)
        logger.info("질문답변 크롤링 시작...")
        await check_new_qna()
        logger.info("질문답변 크롤링 완료")
        
        # 2. 뉴스 크롤링 (동기)
        logger.info("뉴스 크롤링 시작...")
        news = get_news_simple()
        if news:
            send_news_to_discord(news)
        logger.info("뉴스 크롤링 완료")
        
        logger.info("=== 모든 크롤링 작업 완료 ===")
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    # 이벤트 루프 실행
    asyncio.run(run_daily_crawling())

if __name__ == "__main__":
    main()