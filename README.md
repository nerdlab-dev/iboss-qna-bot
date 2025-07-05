# 아이보스 질문답변 디스코드 봇

아이보스(i-boss) 질문답변 게시판의 새로운 게시물을 매일 오전 9시에 크롤링하여 디스코드 채널에 알림을 보내는 봇입니다.

## 기능

- 아이보스 질문답변 게시판 자동 크롤링
- 새로운 질문만 필터링하여 중복 알림 방지
- Discord Embed 형식의 깔끔한 메시지
- 수동 체크 명령어 지원
- 상세한 로깅 시스템

## 설치

### 1. 저장소 클론
```bash
git clone <repository-url>
cd news-crawler-bot
```

### 2. Python 가상환경 설정
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
cp .env.example .env
```
`.env` 파일을 열어 Discord 봇 토큰을 입력하세요.

## 사용법

### 봇 실행
```bash
./run_qna_bot.sh
# 또는
python src/iboss_qna_bot.py
```

### Discord 명령어
- `!test` - 크롤링 테스트
- `!qna` - 수동으로 질문답변 체크

### 자동 실행 설정
매일 오전 9시에 자동 실행하려면 cron을 설정하세요:
```bash
crontab -e
# 다음 줄 추가
0 9 * * * cd /path/to/news-crawler-bot && /usr/bin/python3 src/iboss_qna_bot.py >> logs/cron.log 2>&1
```

## 설정

### channel_config.json
```json
{
    "channels": {
        "qna": {
            "id": "YOUR_DISCORD_CHANNEL_ID",
            "name": "channel-name"
        }
    }
}
```

## 문제 해결

### Chrome 드라이버 오류
```bash
# macOS
brew install --cask chromedriver

# Linux
sudo apt-get install chromium-chromedriver
```

### 봇이 메시지를 보내지 못하는 경우
1. 봇이 채널에 메시지 전송 권한이 있는지 확인
2. 채널 ID가 올바른지 확인
3. Discord Developer Portal에서 봇 권한 확인

## 라이선스

MIT License