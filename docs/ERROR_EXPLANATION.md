# 초기 실행 오류 설명

## 발생한 상황

모니터링 시스템이 Discord로 다음과 같은 오류 메시지를 전송했습니다:

```
🚨 크롤러 오류 감지
총 3개의 문제가 발견되었습니다.

📍 NEWS 크롤러
• missing_log: 로그 파일이 없습니다: /home/nerdlab-datastudio-python/adaptive_news_cron.log

📍 QNA 크롤러
• missing_log: 로그 파일이 없습니다: /home/nerdlab-datastudio-python/adaptive_qna_cron.log
• missing_data: 데이터 파일이 없습니다: /home/nerdlab-datastudio-python/last_qna_adaptive.json
```

## 오류의 의미

### 1. missing_log (로그 파일 없음)
- **의미**: 크롤러가 실행될 때 생성되는 로그 파일이 아직 없다
- **원인**: 크론탭이 설정되었지만 아직 실행 시간이 되지 않음
- **예시**: 오전 8시에 실행되도록 설정했는데, 아직 오전 8시가 되지 않았음

### 2. missing_data (데이터 파일 없음)
- **의미**: 크롤러가 수집한 데이터를 저장하는 파일이 없다
- **원인**: 크롤러가 한 번도 실행되지 않아서 데이터 파일이 생성되지 않음

## 왜 이런 오류가 발생했나?

```
시간 순서:
1. 15:30 - 크롤러 서버 설치 완료
2. 15:35 - 크론탭 설정 (오전 8시, 오후 6시 실행)
3. 16:00 - 모니터링 시스템 첫 실행
4. 16:00 - 오류 감지! (아직 크롤러가 한 번도 실행되지 않음)
```

## 해결 방법

### 수동 실행으로 초기화
```bash
# 뉴스 크롤러 수동 실행
python src/adaptive_news_bot.py

# Q&A 크롤러 수동 실행  
python src/adaptive_qna_bot.py
```

### 결과
- ✅ `adaptive_news_cron.log` 파일 생성
- ✅ `adaptive_qna_cron.log` 파일 생성
- ✅ `last_news_adaptive.json` 파일 생성
- ✅ `last_qna_adaptive.json` 파일 생성
- ✅ 모니터링 상태: "모든 크롤러 정상"

## 앞으로의 동작

1. **자동 실행 스케줄**
   - 뉴스 봇: 매일 오전 8시
   - Q&A 봇: 매일 오후 6시

2. **모니터링**
   - 매시간 정각에 상태 체크
   - 문제 발생 시 Discord 알림

3. **정상 작동 확인**
   - 로그 파일이 25시간 이상 업데이트되지 않으면 알림
   - 크롤링 실패 시 오류 내용과 함께 알림