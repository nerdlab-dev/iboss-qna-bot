#!/usr/bin/env python3
"""
봇을 한 번만 실행하여 즉시 크롤링하고 종료하는 스크립트
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
import discord
from discord.ext import commands
from src.iboss_qna_bot import get_qna_posts, send_qna_to_discord, CHANNEL_CONFIG, load_last_posts, save_last_posts
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} 봇이 시작되었습니다!')
    
    try:
        # 채널 가져오기
        channel_id = CHANNEL_CONFIG['channels']['qna']['id']
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            logger.error(f"채널을 찾을 수 없습니다: {channel_id}")
            await bot.close()
            return
        
        logger.info(f"채널 발견: {channel.name} (ID: {channel.id})")
        
        # 크롤링 실행
        logger.info("크롤링을 시작합니다...")
        
        # 기존 게시물 ID 로드
        last_post_ids = load_last_posts()
        
        # 새로운 게시물 크롤링
        posts = get_qna_posts()
        
        if not posts:
            logger.info("크롤링된 게시물이 없습니다.")
            await bot.close()
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
            logger.info(f"{len(new_posts)}개의 새로운 질문을 발견했습니다.")
            await send_qna_to_discord(new_posts, channel)
        else:
            logger.info("새로운 질문이 없습니다.")
            # 테스트를 위해 최신 게시물 1개만 전송
            logger.info("테스트를 위해 최신 질문 1개를 전송합니다.")
            await send_qna_to_discord(posts[:1], channel)
        
        # 현재 게시물 ID 저장
        save_last_posts(current_post_ids[:10])
        
        logger.info("크롤링이 완료되었습니다.")
        
        # 봇 종료
        await asyncio.sleep(2)  # 메시지 전송 완료 대기
        await bot.close()
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        await bot.close()

async def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다.")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"봇 실행 중 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())