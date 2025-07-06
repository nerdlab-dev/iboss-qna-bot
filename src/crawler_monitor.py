#!/usr/bin/env python3
"""
크롤러 모니터링 및 오류 감지 스크립트
Airflow 없이 단독 실행 가능
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import logging
import subprocess

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/nerdlab-datastudio-python/crawler_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Discord 오류 감지 채널 웹훅
ERROR_WEBHOOK_URL = "https://discord.com/api/webhooks/1391310118850789436/OPWog1Noe8F08Vx19T6Q1TNgo7gMZT7HUQ2czDV-WZ8dhfDXKLmFOHhCM-Ydcbd4ikur"

class CrawlerMonitor:
    def __init__(self):
        self.base_path = '/home/nerdlab-datastudio-python'
        self.monitors = {
            'news': {
                'log_file': f'{self.base_path}/adaptive_news_cron.log',
                'data_file': f'{self.base_path}/last_news_adaptive.json',
                'schedule': '08:00',
                'max_age_hours': 25  # 25시간 이내에 실행되어야 함
            },
            'qna': {
                'log_file': f'{self.base_path}/adaptive_qna_cron.log',
                'data_file': f'{self.base_path}/last_qna_adaptive.json',
                'schedule': '18:00',
                'max_age_hours': 25
            }
        }
        self.errors = []
        
    def check_log_file(self, crawler_type, config):
        """로그 파일 체크"""
        log_file = config['log_file']
        
        if not os.path.exists(log_file):
            self.errors.append({
                'crawler': crawler_type,
                'type': 'missing_log',
                'message': f'로그 파일이 없습니다: {log_file}'
            })
            return False
        
        # 파일 수정 시간 확인
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(log_file))
        if file_age > timedelta(hours=config['max_age_hours']):
            self.errors.append({
                'crawler': crawler_type,
                'type': 'stale_log',
                'message': f'로그가 {file_age.total_seconds()/3600:.1f}시간 동안 업데이트되지 않았습니다'
            })
            return False
        
        # 최근 로그 내용 확인
        try:
            result = subprocess.run(
                ['tail', '-n', '100', log_file],
                capture_output=True,
                text=True
            )
            log_content = result.stdout
            
            # 오류 패턴 확인
            error_patterns = ['ERROR', 'Exception', 'Failed', '실패', '오류']
            errors_found = []
            
            for line in log_content.split('\n')[-20:]:  # 마지막 20줄만 확인
                for pattern in error_patterns:
                    if pattern in line:
                        errors_found.append(line.strip())
            
            if errors_found:
                self.errors.append({
                    'crawler': crawler_type,
                    'type': 'execution_error',
                    'message': f'최근 오류:\n' + '\n'.join(errors_found[-3:])  # 최신 3개만
                })
                return False
                
            # 성공 패턴 확인
            if '디스코드 전송 성공' not in log_content:
                self.errors.append({
                    'crawler': crawler_type,
                    'type': 'no_success',
                    'message': '최근 로그에서 성공 메시지를 찾을 수 없습니다'
                })
                return False
                
        except Exception as e:
            self.errors.append({
                'crawler': crawler_type,
                'type': 'log_read_error',
                'message': f'로그 파일 읽기 오류: {str(e)}'
            })
            return False
        
        return True
    
    def check_data_file(self, crawler_type, config):
        """데이터 파일 체크"""
        data_file = config['data_file']
        
        if not os.path.exists(data_file):
            self.errors.append({
                'crawler': crawler_type,
                'type': 'missing_data',
                'message': f'데이터 파일이 없습니다: {data_file}'
            })
            return False
        
        # 파일 수정 시간 확인
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(data_file))
        if file_age > timedelta(hours=config['max_age_hours']):
            self.errors.append({
                'crawler': crawler_type,
                'type': 'stale_data',
                'message': f'데이터가 {file_age.total_seconds()/3600:.1f}시간 동안 업데이트되지 않았습니다'
            })
            return False
        
        # 데이터 내용 확인
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            if not data or len(data) == 0:
                self.errors.append({
                    'crawler': crawler_type,
                    'type': 'empty_data',
                    'message': '데이터 파일이 비어있습니다'
                })
                return False
                
        except Exception as e:
            self.errors.append({
                'crawler': crawler_type,
                'type': 'data_read_error',
                'message': f'데이터 파일 읽기 오류: {str(e)}'
            })
            return False
        
        return True
    
    def check_process(self, crawler_type):
        """프로세스 실행 상태 확인"""
        try:
            # 현재 실행 중인 크롤러 프로세스 확인
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            process_keywords = {
                'news': 'adaptive_news_bot.py',
                'qna': 'adaptive_qna_bot.py'
            }
            
            keyword = process_keywords.get(crawler_type)
            if keyword and keyword in result.stdout:
                logger.info(f"{crawler_type} 크롤러가 현재 실행 중입니다")
                return True
                
        except Exception as e:
            logger.error(f"프로세스 확인 오류: {str(e)}")
        
        return False
    
    def send_error_notification(self):
        """Discord로 오류 알림 전송"""
        if not self.errors:
            return
        
        # 오류별로 그룹화
        error_by_crawler = {}
        for error in self.errors:
            crawler = error['crawler']
            if crawler not in error_by_crawler:
                error_by_crawler[crawler] = []
            error_by_crawler[crawler].append(error)
        
        # 임베드 생성
        embeds = []
        
        main_embed = {
            "title": "🚨 크롤러 오류 감지",
            "description": f"총 {len(self.errors)}개의 문제가 발견되었습니다.",
            "color": 15158332,  # 빨간색
            "timestamp": datetime.now().isoformat(),
            "fields": [],
            "footer": {
                "text": "크롤러 모니터링 시스템"
            }
        }
        
        for crawler, errors in error_by_crawler.items():
            error_messages = []
            for error in errors:
                error_messages.append(f"• **{error['type']}**: {error['message']}")
            
            main_embed["fields"].append({
                "name": f"📍 {crawler.upper()} 크롤러",
                "value": '\n'.join(error_messages)[:1024],
                "inline": False
            })
        
        # 권장 조치사항 추가
        main_embed["fields"].append({
            "name": "🔧 권장 조치사항",
            "value": "1. 서버 로그 확인: `tail -f /home/nerdlab-datastudio-python/*_cron.log`\n"
                     "2. 수동 실행 테스트: `python src/adaptive_*_bot.py`\n"
                     "3. HTML 구조 변경 확인: `html_patterns.json` 확인",
            "inline": False
        })
        
        embeds.append(main_embed)
        
        # Discord 웹훅으로 전송
        data = {
            "embeds": embeds,
            "username": "크롤러 모니터링"
        }
        
        try:
            response = requests.post(ERROR_WEBHOOK_URL, json=data)
            if response.status_code == 204:
                logger.info("오류 알림 전송 성공")
            else:
                logger.error(f"오류 알림 전송 실패: {response.status_code}")
        except Exception as e:
            logger.error(f"Discord 전송 오류: {str(e)}")
    
    def send_success_notification(self):
        """정상 작동 알림 (주 1회)"""
        # 일요일 오전 9시에만 전송
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 9:
            embed = {
                "title": "✅ 크롤러 정상 작동 중",
                "description": "모든 크롤러가 정상적으로 작동하고 있습니다.",
                "color": 5763719,  # 초록색
                "timestamp": now.isoformat(),
                "fields": [
                    {
                        "name": "뉴스 크롤러",
                        "value": "매일 오전 8시 정상 실행",
                        "inline": True
                    },
                    {
                        "name": "Q&A 크롤러",
                        "value": "매일 오후 6시 정상 실행",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "주간 상태 리포트"
                }
            }
            
            data = {
                "embeds": [embed],
                "username": "크롤러 모니터링"
            }
            
            try:
                requests.post(ERROR_WEBHOOK_URL, json=data)
            except:
                pass
    
    def run(self):
        """모니터링 실행"""
        logger.info("크롤러 모니터링 시작")
        
        all_healthy = True
        
        for crawler_type, config in self.monitors.items():
            logger.info(f"{crawler_type} 크롤러 체크 중...")
            
            # 각 체크 수행
            log_ok = self.check_log_file(crawler_type, config)
            data_ok = self.check_data_file(crawler_type, config)
            
            if not (log_ok and data_ok):
                all_healthy = False
            
            # 현재 실행 중인지 확인
            self.check_process(crawler_type)
        
        # 결과 처리
        if self.errors:
            logger.warning(f"{len(self.errors)}개의 오류 발견")
            self.send_error_notification()
        else:
            logger.info("모든 크롤러 정상")
            self.send_success_notification()
        
        return all_healthy

if __name__ == "__main__":
    monitor = CrawlerMonitor()
    success = monitor.run()
    sys.exit(0 if success else 1)