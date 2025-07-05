# 아이보스 질문답변 봇 설치 가이드

## 1. 환경 설정

### 1.1 Python 가상환경 생성
```bash
cd /Users/jaewansim/Documents/nerdlab/news-crawler-bot
python3 -m venv venv
source venv/bin/activate
```

### 1.2 의존성 설치
```bash
pip install -r requirements.txt
```

### 1.3 환경변수 설정
```bash
cp .env.example .env
```
`.env` 파일을 열어 Discord 봇 토큰을 입력하세요.

## 2. Discord 봇 설정

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 새 애플리케이션 생성
2. Bot 섹션에서 봇 생성 및 토큰 복사
3. OAuth2 > URL Generator에서:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`
4. 생성된 URL로 봇을 서버에 초대

## 3. 봇 실행

### 3.1 수동 실행
```bash
./run_qna_bot.sh
```

### 3.2 테스트
봇이 실행된 후 Discord 채널에서:
- `!test` - 크롤링 테스트
- `!qna` - 수동으로 질문답변 체크

## 4. 자동 실행 설정 (cron)

### 4.1 crontab 편집
```bash
crontab -e
```

### 4.2 매일 오전 9시 실행 설정
```cron
# 아이보스 질문답변 봇 (매일 오전 9시)
0 9 * * * cd /Users/jaewansim/Documents/nerdlab/news-crawler-bot && /usr/bin/python3 src/iboss_qna_bot.py >> logs/cron.log 2>&1
```

### 4.3 LaunchAgent 설정 (macOS 권장)
`~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nerdlab.iboss-qna-bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/jaewansim/Documents/nerdlab/news-crawler-bot/src/iboss_qna_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/jaewansim/Documents/nerdlab/news-crawler-bot</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/jaewansim/Documents/nerdlab/news-crawler-bot/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/jaewansim/Documents/nerdlab/news-crawler-bot/logs/launchd.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

LaunchAgent 로드:
```bash
launchctl load ~/Library/LaunchAgents/com.nerdlab.iboss-qna-bot.plist
```

## 5. 로그 확인

- 봇 로그: `bot.log`
- cron 로그: `logs/cron.log`
- LaunchAgent 로그: `logs/launchd.out.log`, `logs/launchd.err.log`

## 6. 문제 해결

### Chrome 드라이버 문제
```bash
# Chrome 브라우저 설치 확인
which google-chrome || which chromium

# 수동으로 ChromeDriver 설치
brew install --cask chromedriver
```

### 권한 문제
```bash
# 실행 권한 부여
chmod +x run_qna_bot.sh
chmod +x src/iboss_qna_bot.py
```

### 봇이 메시지를 보내지 못하는 경우
1. 봇이 채널에 접근 권한이 있는지 확인
2. `channel_config.json`의 채널 ID가 올바른지 확인
3. Discord 개발자 포털에서 Intents 설정 확인