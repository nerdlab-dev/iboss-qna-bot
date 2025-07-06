#!/usr/bin/env python3
"""
서버용 뉴스 크롤링 봇 - 헤드리스 환경 최적화
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_chrome_driver():
    """서버용 Chrome 웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 서버에서는 chromium-driver 직접 사용
    service = Service('/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=chrome_options)

# iboss_news_login의 함수들을 import
from src.iboss_news_login import login_to_iboss, get_news_with_login, send_news_to_discord, check_and_send_news

# get_chrome_driver 함수를 서버용으로 오버라이드
import src.iboss_news_login
src.iboss_news_login.get_chrome_driver = get_chrome_driver

if __name__ == "__main__":
    try:
        logger.info("서버 뉴스 크롤링 시작")
        check_and_send_news()
        logger.info("서버 뉴스 크롤링 완료")
    except Exception as e:
        logger.error(f"서버 크롤링 오류: {str(e)}")
        import traceback
        traceback.print_exc()