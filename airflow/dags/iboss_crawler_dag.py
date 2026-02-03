"""
아이보스 크롤러 Airflow DAG - 오류 감지 및 알림
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
import requests
import logging
import json
import os

# Discord 오류 감지 채널 웹훅
ERROR_WEBHOOK_URL = "https://discord.com/api/webhooks/1391310118850789436/OPWog1Noe8F08Vx19T6Q1TNgo7gMZT7HUQ2czDV-WZ8dhfDXKLmFOHhCM-Ydcbd4ikur"

# 기본 설정
default_args = {
    'owner': 'nerdlab',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 7),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def send_error_notification(context):
    """오류 발생 시 Discord로 알림"""
    task_instance = context['task_instance']
    task_id = task_instance.task_id
    dag_id = context['dag'].dag_id
    execution_date = context['execution_date']
    exception = context.get('exception', 'Unknown error')
    
    # 오류 메시지 생성
    embed = {
        "title": "🚨 크롤링 오류 감지",
        "description": f"**{dag_id}**의 **{task_id}** 작업에서 오류가 발생했습니다.",
        "color": 15158332,  # 빨간색
        "fields": [
            {
                "name": "작업 ID",
                "value": task_id,
                "inline": True
            },
            {
                "name": "실행 시간",
                "value": execution_date.strftime('%Y-%m-%d %H:%M:%S'),
                "inline": True
            },
            {
                "name": "재시도 횟수",
                "value": f"{task_instance.try_number}/{task_instance.max_tries}",
                "inline": True
            },
            {
                "name": "오류 내용",
                "value": f"```{str(exception)[:1000]}```",
                "inline": False
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "footer": {
            "text": "Airflow 오류 감지 시스템"
        }
    }
    
    # Discord 웹훅으로 전송
    data = {
        "embeds": [embed],
        "username": "크롤러 오류 감지봇"
    }
    
    try:
        response = requests.post(ERROR_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            logging.info("오류 알림 전송 성공")
        else:
            logging.error(f"오류 알림 전송 실패: {response.status_code}")
    except Exception as e:
        logging.error(f"Discord 전송 오류: {str(e)}")

def check_crawler_health(**context):
    """크롤러 상태 체크"""
    import subprocess
    import json
    
    health_status = {
        'news_crawler': {'status': 'unknown', 'last_run': None, 'error': None},
        'qna_crawler': {'status': 'unknown', 'last_run': None, 'error': None}
    }
    
    # 로그 파일 확인
    log_files = {
        'news': '/home/nerdlab-datastudio-python/adaptive_news_cron.log',
        'qna': '/home/nerdlab-datastudio-python/adaptive_qna_cron.log'
    }
    
    for crawler_type, log_file in log_files.items():
        try:
            # 로그 파일의 마지막 100줄 확인
            if os.path.exists(log_file):
                result = subprocess.run(
                    ['tail', '-n', '100', log_file],
                    capture_output=True,
                    text=True
                )
                
                log_content = result.stdout
                
                # 성공/실패 패턴 확인
                if '디스코드 전송 성공' in log_content:
                    health_status[f'{crawler_type}_crawler']['status'] = 'success'
                elif 'ERROR' in log_content or '오류' in log_content:
                    health_status[f'{crawler_type}_crawler']['status'] = 'error'
                    # 오류 메시지 추출
                    error_lines = [line for line in log_content.split('\n') if 'ERROR' in line or '오류' in line]
                    if error_lines:
                        health_status[f'{crawler_type}_crawler']['error'] = error_lines[-1]
                
                # 마지막 실행 시간 확인
                last_modified = os.path.getmtime(log_file)
                health_status[f'{crawler_type}_crawler']['last_run'] = datetime.fromtimestamp(last_modified).isoformat()
        
        except Exception as e:
            health_status[f'{crawler_type}_crawler']['error'] = str(e)
    
    # 상태를 XCom으로 전달
    context['task_instance'].xcom_push(key='health_status', value=health_status)
    
    # 오류가 있으면 예외 발생
    errors = []
    for crawler, status in health_status.items():
        if status['status'] == 'error':
            errors.append(f"{crawler}: {status.get('error', 'Unknown error')}")
    
    if errors:
        raise Exception("크롤러 오류 감지:\n" + "\n".join(errors))
    
    return health_status

def run_news_crawler(**context):
    """뉴스 크롤러 실행"""
    import subprocess
    
    cmd = [
        '/home/nerdlab-datastudio-python/news-venv/bin/python',
        '/home/nerdlab-datastudio-python/src/adaptive_news_bot.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd='/home/nerdlab-datastudio-python')
    
    if result.returncode != 0:
        raise Exception(f"뉴스 크롤러 실행 실패:\n{result.stderr}")
    
    logging.info(f"뉴스 크롤러 실행 성공:\n{result.stdout}")
    return True

def run_qna_crawler(**context):
    """Q&A 크롤러 실행"""
    import subprocess
    
    cmd = [
        '/home/nerdlab-datastudio-python/news-venv/bin/python',
        '/home/nerdlab-datastudio-python/src/adaptive_qna_bot.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd='/home/nerdlab-datastudio-python')
    
    if result.returncode != 0:
        raise Exception(f"Q&A 크롤러 실행 실패:\n{result.stderr}")
    
    logging.info(f"Q&A 크롤러 실행 성공:\n{result.stdout}")
    return True

def validate_crawled_data(**context):
    """크롤링된 데이터 검증"""
    task_instance = context['task_instance']
    crawler_type = context['params'].get('crawler_type', 'news')
    
    # 마지막 저장된 데이터 확인
    if crawler_type == 'news':
        data_file = '/home/nerdlab-datastudio-python/last_news_adaptive.json'
    else:
        data_file = '/home/nerdlab-datastudio-python/last_qna_adaptive.json'
    
    if not os.path.exists(data_file):
        raise Exception(f"{crawler_type} 데이터 파일이 없습니다: {data_file}")
    
    # 데이터 로드 및 검증
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    if not data or len(data) == 0:
        raise Exception(f"{crawler_type} 크롤링 데이터가 비어있습니다")
    
    # 데이터 최신성 확인 (파일 수정 시간이 1시간 이내인지)
    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(data_file))
    if file_age > timedelta(hours=1):
        raise Exception(f"{crawler_type} 데이터가 오래되었습니다: {file_age}")
    
    logging.info(f"{crawler_type} 데이터 검증 성공: {len(data)}개 항목")
    return True

# DAG 정의
dag = DAG(
    'iboss_crawler_monitoring',
    default_args=default_args,
    description='아이보스 크롤러 모니터링 및 오류 감지',
    schedule_interval='0 */3 * * *',  # 3시간마다 실행
    catchup=False,
    on_failure_callback=send_error_notification,
    tags=['crawler', 'monitoring', 'iboss'],
)

# 뉴스 크롤러 DAG (오전 8시)
news_dag = DAG(
    'iboss_news_crawler',
    default_args=default_args,
    description='아이보스 뉴스 크롤러',
    schedule_interval='0 8 * * *',
    catchup=False,
    on_failure_callback=send_error_notification,
    tags=['crawler', 'news', 'iboss'],
)

# Q&A 크롤러 DAG (오후 6시)
qna_dag = DAG(
    'iboss_qna_crawler',
    default_args=default_args,
    description='아이보스 Q&A 크롤러',
    schedule_interval='0 18 * * *',
    catchup=False,
    on_failure_callback=send_error_notification,
    tags=['crawler', 'qna', 'iboss'],
)

# 모니터링 태스크
health_check = PythonOperator(
    task_id='check_crawler_health',
    python_callable=check_crawler_health,
    dag=dag,
)

# 뉴스 크롤러 태스크
news_crawler = PythonOperator(
    task_id='run_news_crawler',
    python_callable=run_news_crawler,
    dag=news_dag,
    on_failure_callback=send_error_notification,
)

news_validation = PythonOperator(
    task_id='validate_news_data',
    python_callable=validate_crawled_data,
    params={'crawler_type': 'news'},
    dag=news_dag,
)

# Q&A 크롤러 태스크
qna_crawler = PythonOperator(
    task_id='run_qna_crawler',
    python_callable=run_qna_crawler,
    dag=qna_dag,
    on_failure_callback=send_error_notification,
)

qna_validation = PythonOperator(
    task_id='validate_qna_data',
    python_callable=validate_crawled_data,
    params={'crawler_type': 'qna'},
    dag=qna_dag,
)

# 태스크 의존성 설정
news_crawler >> news_validation
qna_crawler >> qna_validation