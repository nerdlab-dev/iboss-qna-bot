#!/bin/bash
# Airflow 설치 및 설정 스크립트

echo "Airflow 설치 시작..."

# Airflow 홈 디렉토리 설정
export AIRFLOW_HOME=/home/nerdlab-datastudio-python/airflow

# Python 가상환경 생성
python3 -m venv airflow-venv
source airflow-venv/bin/activate

# Airflow 설치
pip install --upgrade pip
pip install apache-airflow==2.8.0
pip install requests beautifulsoup4 selenium

# Airflow DB 초기화
airflow db init

# Airflow 사용자 생성
airflow users create \
    --username admin \
    --password admin123 \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@nerdlab.com

# DAG 디렉토리 생성
mkdir -p $AIRFLOW_HOME/dags

# 서비스 파일 생성
cat > /etc/systemd/system/airflow-webserver.service << EOF
[Unit]
Description=Airflow webserver daemon
After=network.target

[Service]
Environment="AIRFLOW_HOME=/home/nerdlab-datastudio-python/airflow"
User=root
Group=root
Type=simple
ExecStart=/home/nerdlab-datastudio-python/airflow-venv/bin/airflow webserver --port 8080
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/airflow-scheduler.service << EOF
[Unit]
Description=Airflow scheduler daemon
After=network.target

[Service]
Environment="AIRFLOW_HOME=/home/nerdlab-datastudio-python/airflow"
User=root
Group=root
Type=simple
ExecStart=/home/nerdlab-datastudio-python/airflow-venv/bin/airflow scheduler
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
systemctl daemon-reload
systemctl enable airflow-webserver
systemctl enable airflow-scheduler
systemctl start airflow-webserver
systemctl start airflow-scheduler

echo "Airflow 설치 완료!"
echo "웹 UI: http://서버IP:8080"
echo "사용자: admin / 비밀번호: admin123"