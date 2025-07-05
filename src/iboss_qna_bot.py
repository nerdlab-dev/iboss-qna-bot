import os
import json
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
from datetime import datetime, time as dt_time, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 채널 설정 로드
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'channel_config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    CHANNEL_CONFIG = json.load(f)

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 마지막으로 확인한 게시물 ID를 저장할 파일
LAST_POST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'last_qna_posts.json')

def load_last_posts():
    """마지막 게시물 ID 로드"""
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, 'r') as f:
            return json.load(f)
    return []

def save_last_posts(post_ids):
    """마지막 게시물 ID 저장"""
    with open(LAST_POST_FILE, 'w') as f:
        json.dump(post_ids, f)

def get_chrome_driver():
    """Chrome 웹드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_qna_posts():
    """아이보스 질문답변 게시판 크롤링"""
    logger.info("아이보스 질문답변 크롤링 시작")
    url = "https://www.i-boss.co.kr/ab-2109"
    
    driver = None
    try:
        driver = get_chrome_driver()
        logger.info(f"URL 접속: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.contents")))
        time.sleep(2)  # 추가 로딩 대기
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        posts = []
        # 질문 목록 찾기
        questions = soup.select('div.article')
        
        if not questions:
            logger.warning("질문을 찾을 수 없습니다.")
            return []
        
        logger.info(f"총 {len(questions)}개의 질문 발견")
        
        for idx, question in enumerate(questions[:10], 1):  # 최신 10개만
            try:
                # 제목과 링크
                title_element = question.select_one('div.content a')
                if not title_element:
                    continue
                
                title = title_element.text.strip()
                link = title_element.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.i-boss.co.kr{link}"
                
                # 게시물 ID 추출
                post_id = ''
                # onclick 속성에서 ID 추출
                onclick = question.get('onclick', '')
                if onclick:
                    match = re.search(r'viewDetail\([\'"]([^\'"]+)', onclick)
                    if match:
                        post_id = match.group(1)
                
                # ID가 없으면 링크에서 추출
                if not post_id and link:
                    match = re.search(r'ab-2109-(\d+)', link)
                    if match:
                        post_id = match.group(1)
                
                # 그래도 없으면 생성
                if not post_id:
                    post_id = f"qna_{idx}_{datetime.now().strftime('%Y%m%d%H%M')}"
                
                # 내용 요약
                content = ''
                content_elements = question.select('div.content')
                if content_elements:
                    content_text = content_elements[0].get_text(separator=' ', strip=True)
                    # 제목을 제외한 내용 추출
                    content = content_text.replace(title, '').strip()
                
                # 태그
                tags = []
                hashtag_element = question.select_one('p.hashtag')
                if hashtag_element:
                    tags = [tag.strip() for tag in hashtag_element.text.split('#') if tag.strip()]
                
                # 작성자와 날짜
                author = ''
                date = ''
                info_element = question.select_one('div.info')
                if info_element:
                    info_text = info_element.text.strip()
                    # "작성자 | 날짜" 형식 파싱
                    if '|' in info_text:
                        parts = info_text.split('|')
                        author = parts[0].strip()
                        date = parts[-1].strip()
                    else:
                        # 공백으로 구분
                        info_parts = info_text.split()
                        if len(info_parts) >= 2:
                            author = info_parts[0]
                            date = ' '.join(info_parts[1:])
                
                post_data = {
                    'id': post_id,
                    'title': title,
                    'link': link,
                    'author': author,
                    'date': date,
                    'content': content[:200] + '...' if len(content) > 200 else content,
                    'tags': tags
                }
                posts.append(post_data)
                logger.debug(f"질문 {idx} 처리 완료: {title}")
                
            except Exception as e:
                logger.error(f"질문 {idx} 처리 중 오류: {str(e)}")
                continue
        
        logger.info(f"총 {len(posts)}개의 질문 수집 완료")
        return posts
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()

async def send_qna_to_discord(posts, channel):
    """디스코드 채널에 질문답변 전송"""
    if not posts:
        logger.info("전송할 새로운 질문이 없습니다.")
        return
    
    logger.info(f"{len(posts)}개의 새로운 질문을 전송합니다.")
    
    embed = discord.Embed(
        title="📢 아이보스 새로운 질문",
        description=f"{len(posts)}개의 새로운 질문이 등록되었습니다.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for i, post in enumerate(posts[:3]):  # 최대 3개까지만 임베드에 표시
        field_value = ""
        if post.get('content'):
            field_value += f"{post['content'][:100]}...\n"
        if post.get('author'):
            field_value += f"작성자: {post['author']}"
        if post.get('date'):
            field_value += f" | {post['date']}"
        field_value += f"\n[자세히 보기]({post['link']})"
        
        # 제목이 너무 길면 잘라내기 (Discord 제한: 256자)
        title = post['title']
        if len(title) > 250:
            title = title[:247] + "..."
        
        embed.add_field(
            name=f"{i+1}. {title}",
            value=field_value,
            inline=False
        )
    
    if len(posts) > 3:
        embed.add_field(
            name="추가 질문",
            value=f"외 {len(posts)-3}개의 질문이 더 있습니다.",
            inline=False
        )
    
    embed.set_footer(text="아이보스 질문답변 게시판")
    
    try:
        await channel.send(embed=embed)
        logger.info("디스코드 메시지 전송 완료")
    except Exception as e:
        logger.error(f"디스코드 메시지 전송 실패: {str(e)}")

async def check_new_qna():
    """새로운 질문 확인 및 알림"""
    channel_id = CHANNEL_CONFIG['channels']['qna']['id']
    channel = bot.get_channel(int(channel_id))
    
    if not channel:
        logger.error(f"채널을 찾을 수 없습니다: {channel_id}")
        return
    
    # 기존 게시물 ID 로드
    last_post_ids = load_last_posts()
    
    # 새로운 게시물 크롤링
    posts = get_qna_posts()
    
    if not posts:
        logger.info("크롤링된 게시물이 없습니다.")
        return
    
    # 새로운 게시물만 필터링
    new_posts = []
    current_post_ids = []
    
    for post in posts:
        current_post_ids.append(post['id'])
        if post['id'] not in last_post_ids:
            new_posts.append(post)
    
    # 새로운 게시물 전송
    if new_posts:
        await send_qna_to_discord(new_posts, channel)
    else:
        logger.info("새로운 질문이 없습니다.")
    
    # 현재 게시물 ID 저장
    save_last_posts(current_post_ids[:10])  # 최신 10개만 저장

@bot.event
async def on_ready():
    logger.info(f'{bot.user} 봇이 시작되었습니다!')
    # 스케줄러 시작
    check_qna_task.start()

@tasks.loop(time=dt_time(8, 0))  # 매일 오전 8시
async def check_qna_task():
    logger.info("정기 질문답변 체크 시작")
    await check_new_qna()

@bot.command(name='qna')
async def manual_check(ctx):
    """수동으로 질문답변 체크"""
    logger.info(f"수동 체크 요청: {ctx.author}")
    await ctx.send("질문답변 게시판을 확인합니다...")
    await check_new_qna()
    await ctx.send("확인 완료!")

@bot.command(name='test')
async def test_crawl(ctx):
    """크롤링 테스트"""
    await ctx.send("크롤링 테스트를 시작합니다...")
    posts = get_qna_posts()
    if posts:
        await ctx.send(f"✅ 크롤링 성공! {len(posts)}개의 질문을 찾았습니다.")
        await ctx.send(f"최신 질문: {posts[0]['title']}")
    else:
        await ctx.send("❌ 크롤링 실패 또는 질문을 찾을 수 없습니다.")

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다.")
        exit(1)
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"봇 실행 중 오류: {str(e)}")