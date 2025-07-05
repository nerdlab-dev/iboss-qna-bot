#!/usr/bin/env python3
"""
봇이 접근 가능한 서버와 채널 목록을 확인하는 스크립트
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
import discord
from discord.ext import commands
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
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} 봇이 시작되었습니다!')
    
    print("\n=== 봇이 접근 가능한 서버 및 채널 목록 ===\n")
    
    for guild in bot.guilds:
        print(f"서버: {guild.name} (ID: {guild.id})")
        print("  채널 목록:")
        
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            can_send = "✅" if permissions.send_messages else "❌"
            print(f"    {can_send} #{channel.name} (ID: {channel.id})")
        
        print()
    
    print("=== 채널 권한 설명 ===")
    print("✅ = 메시지 전송 가능")
    print("❌ = 메시지 전송 불가 (권한 설정 필요)")
    print()
    print("위 채널 ID 중 하나를 channel_config.json에 설정하세요.")
    
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