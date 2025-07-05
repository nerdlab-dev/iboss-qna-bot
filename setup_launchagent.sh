#!/bin/bash

echo "LaunchAgent 설정을 시작합니다..."

# LaunchAgents 디렉토리 생성 (없는 경우)
mkdir -p ~/Library/LaunchAgents

# plist 파일 복사
cp com.nerdlab.iboss-qna-bot.plist ~/Library/LaunchAgents/

# 기존 agent 언로드 (있는 경우)
launchctl unload ~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist 2>/dev/null

# 새 agent 로드
launchctl load ~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist

echo "LaunchAgent가 설정되었습니다."
echo ""
echo "상태 확인:"
launchctl list | grep com.nerdlab.iboss-qna-bot
echo ""
echo "제거하려면:"
echo "launchctl unload ~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist"
echo "rm ~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist"