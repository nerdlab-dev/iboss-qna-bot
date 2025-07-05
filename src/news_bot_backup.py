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

# 환경 변수 로드
load_dotenv()

# 채널 설정 로드
with open('channel_config.json', 'r', encoding='utf-8') as f:
    CHANNEL_CONFIG = json.load(f)

# 디스코드 봇 설정
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# 마지막으로 확인한 게시물 ID를 저장할 변수들
last_post_ids = {
    'qna': None,
    'news': None,
    'yozm': None
}

# 마지막 실행 시간을 저장할 변수들
last_run_times = {
    'qna': None,
    'news': None,
    'yozm': None
}

# 태스크 실행 상태를 저장할 변수
tasks_running = {
    'qna': False,
    'news': False,
    'yozm': False
}

# 메시지 타입별 이름 정의
type_names = {
    'qna': '새로운 질문',
    'news': '새로운 뉴스',
    'yozm': '요즘IT 새 글'
}

# 질문답변 크롤링 함수
def get_qna_posts():
    print("\n=== 질문답변 크롤링 디버그 정보 ===")
    print("시작 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    url = "https://www.i-boss.co.kr/ab-2109"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
    
    print("질문답변 크롤링 시작...")
    try:
        session = requests.Session()
        print(f"URL 접속 시도: {url}")
        response = session.get(url, headers=headers, timeout=10, verify=False)
        print(f"응답 상태 코드: {response.status_code}")
        
        # 디버그용 HTML 저장
        with open('qna_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("페이지 소스가 qna_debug.html에 저장되었습니다.")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        # 다양한 선택자 시도
        selectors = [
            'div.contents div.article.stateE',
            'div.article.stateE',
            'div.article',
            'div[class*="article"]',
            'div[class*="stateE"]'
        ]
        
        for selector in selectors:
            print(f"\n선택자 '{selector}'로 질문 검색 중...")
            questions = soup.select(selector)
            if questions:
                print(f"선택자 '{selector}'로 {len(questions)}개의 질문 발견")
                break
        
        if not questions:
            print("경고: 어떤 선택자로도 질문을 찾을 수 없습니다.")
            return []
        
        print(f"\n질문 파싱 시작 (총 {len(questions)}개)")
        for idx, question in enumerate(questions, 1):
            try:
                print(f"\n질문 {idx}/{len(questions)} 처리 중...")
                
                # 제목과 링크
                title_element = question.select_one('div.content a')
                if not title_element:
                    print(f"질문 {idx}: 제목 요소를 찾을 수 없음")
                    continue
                    
                title = title_element.text.strip()
                link = title_element['href']
                if not link.startswith('http'):
                    link = f"https://www.i-boss.co.kr{link}"
                
                print(f"질문 {idx} 제목: {title}")
                print(f"질문 {idx} 링크: {link}")
                
                # 내용
                content = ''
                content_element = question.select_one('div.content strong')
                if content_element:
                    content = content_element.text.strip()
                    print(f"질문 {idx} 내용: {content[:50]}...")
                
                # 태그
                tags = []
                hashtag_element = question.select_one('p.hashtag')
                if hashtag_element:
                    tags = [tag.strip() for tag in hashtag_element.text.split('#') if tag.strip()]
                    print(f"질문 {idx} 태그: {tags}")
                
                # 작성자와 날짜
                author = ''
                date = ''
                info_element = question.select_one('div.info')
                if info_element:
                    info_text = info_element.text.strip()
                    info_parts = info_text.split()
                    if len(info_parts) >= 2:
                        author = info_parts[0]
                        date = info_parts[-1]
                        print(f"질문 {idx} 작성자: {author}")
                        print(f"질문 {idx} 날짜: {date}")
                
                post_data = {
                    'id': question.get('id', str(len(posts))),
                    'title': title,
                    'link': link,
                    'author': author,
                    'date': date,
                    'content': content,
                    'tags': tags
                }
                posts.append(post_data)
                print(f"질문 {idx} 처리 완료")
                
            except Exception as e:
                print(f"질문 {idx} 처리 중 오류 발생: {str(e)}")
                continue
        
        print(f"\n최종 수집된 질문 수: {len(posts)}")
        return posts
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc())
        return []

# 뉴스 크롤링 함수
def get_news_posts():
    print("\n=== 뉴스 크롤링 디버그 정보 ===")
    print("시작 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # 웹드라이버 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            print("웹드라이버 초기화 완료")
            url = "https://www.i-boss.co.kr/ab-7214"
            print(f"URL 접속 시도: {url}")
            driver.get(url)
            
            # 페이지 로딩 대기
            wait = WebDriverWait(driver, 10)
            print("페이지 로딩 대기 중...")
            
            # 뉴스 기사가 로드될 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.article")))
                print("뉴스 기사 요소 발견")
            except Exception as e:
                print(f"뉴스 기사 요소 대기 중 오류: {str(e)}")
                # 대체 선택자 시도
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))
                    print("대체 선택자로 뉴스 기사 요소 발견")
                except Exception as e:
                    print(f"대체 선택자로도 요소를 찾을 수 없음: {str(e)}")
            
            # 페이지 소스 저장 (디버깅용)
            with open('selenium_debug.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("페이지 소스가 selenium_debug.html에 저장되었습니다.")
            
            # 뉴스 기사 수집
            posts = []
            selectors = [
                "div.article",
                "article",
                "div[class*='article']",
                "div[class*='news']",
                "div[class*='post']"
            ]
            
            for selector in selectors:
                print(f"선택자 '{selector}'로 기사 검색 중...")
                articles = driver.find_elements(By.CSS_SELECTOR, selector)
                if articles:
                    print(f"선택자 '{selector}'로 {len(articles)}개의 기사 발견")
                    break
            
            if not articles:
                print("경고: 어떤 선택자로도 뉴스 기사를 찾을 수 없습니다.")
                return []
            
            print(f"\n기사 파싱 시작 (총 {len(articles)}개)")
            for idx, article in enumerate(articles, 1):
                try:
                    print(f"\n기사 {idx}/{len(articles)} 처리 중...")
                    
                    # 제목과 링크
                    title_elements = article.find_elements(By.CSS_SELECTOR, "a, h2, h3, .title")
                    if not title_elements:
                        print(f"기사 {idx}: 제목 요소를 찾을 수 없음")
                        continue
                        
                    title_element = title_elements[0]
                    title = title_element.text.strip()
                    link = title_element.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://www.i-boss.co.kr{link}"
                    
                    print(f"기사 {idx} 제목: {title}")
                    print(f"기사 {idx} 링크: {link}")
                    
                    # 시간 정보 - 다양한 선택자 시도
                    time_selectors = [
                        ".time",
                        ".date",
                        ".post-date",
                        "time",
                        "span[class*='date']",
                        "span[class*='time']",
                        "div[class*='date']",
                        "div[class*='time']",
                        "p[class*='date']",
                        "p[class*='time']"
                    ]
                    
                    post_time = ''
                    for time_selector in time_selectors:
                        time_elements = article.find_elements(By.CSS_SELECTOR, time_selector)
                        if time_elements:
                            post_time = time_elements[0].text.strip()
                            print(f"기사 {idx} 시간 정보 발견: {post_time}")
                            break
                    
                    # 시간 정보가 없으면 부모 요소에서 찾기
                    if not post_time:
                        print(f"기사 {idx}: 직접적인 시간 정보를 찾을 수 없음, 부모 요소 검색 중...")
                        try:
                            parent = article.find_element(By.XPATH, "./..")
                            for time_selector in time_selectors:
                                time_elements = parent.find_elements(By.CSS_SELECTOR, time_selector)
                                if time_elements:
                                    post_time = time_elements[0].text.strip()
                                    print(f"기사 {idx} 부모 요소에서 시간 정보 발견: {post_time}")
                                    break
                        except Exception as e:
                            print(f"기사 {idx} 부모 요소 검색 중 오류: {str(e)}")
                    
                    post_data = {
                        'id': article.get_attribute('id') or str(len(posts)),
                        'title': title,
                        'link': link,
                        'time': post_time
                    }
                    posts.append(post_data)
                    print(f"기사 {idx} 처리 완료")
                    
                except Exception as e:
                    print(f"기사 {idx} 처리 중 오류 발생: {str(e)}")
                    continue
            
            print(f"\n최종 수집된 뉴스 수: {len(posts)}")
            return posts
            
        finally:
            print("웹드라이버 종료 중...")
            driver.quit()
            print("웹드라이버 종료 완료")
            
    except Exception as e:
        print(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc())
        return []

# 요즘IT 크롤링 함수
def get_yozm_posts():
    url = "https://yozm.wishket.com/magazine/list/develop/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print("요즘IT 크롤링 시작...")
    try:
        response = requests.get(url, headers=headers)
        print(f"응답 상태 코드: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = []
        
        # 개발 관련 글 목록 찾기 (선택자 업데이트)
        articles = soup.select('div.item-list-wrapper article')
        print(f"\n찾은 글 수: {len(articles)}")
        
        for article in articles:
            try:
                # 제목과 링크
                title_element = article.select_one('h2.item-title a')
                if title_element:
                    title = title_element.text.strip()
                    link = f"https://yozm.wishket.com{title_element['href']}"
                    
                    # 요약 내용
                    description = article.select_one('p.item-description')
                    content = description.text.strip() if description else ''
                    
                    post_data = {
                        'title': title,
                        'link': link,
                        'content': content
                    }
                    posts.append(post_data)
            except Exception as e:
                print(f"글 파싱 중 오류 발생: {e}")
                continue
        
        return posts
    except Exception as e:
        print(f"요즘IT 크롤링 중 오류 발생: {e}")
        return []

# 게시물 전송 함수
async def send_posts_to_channel(posts, channel, post_type):
    try:
        if not channel:
            print(f"오류: 채널이 None입니다. 채널 ID: {channel.id if hasattr(channel, 'id') else 'unknown'}")
            return
            
        if not posts:
            print(f"전송할 {type_names[post_type]}이 없습니다.")
            return
            
        print(f"\n=== {type_names[post_type]} 메시지 전송 시작 ===")
        print(f"전송할 게시물 수: {len(posts)}")
        print(f"대상 채널: {channel.name} (ID: {channel.id})")
        
        message = f"**📢 {type_names[post_type]} 목록**\n\n"
        
        for post in posts[:5]:  # 최대 5개까지만 전송
            print(f"\n게시물 처리 중: {post['title']}")
            message += f"**제목:** {post['title']}\n"
            if post_type == 'qna':
                if post.get('content'):
                    summary = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
                    message += f"**내용:** {summary}\n"
                if post.get('author'):
                    message += f"**작성자:** {post['author']}\n"
                if post.get('date'):
                    message += f"**날짜:** {post['date']}\n"
                if post.get('tags'):
                    message += f"**태그:** #{' #'.join(post['tags'])}\n"
            elif post_type == 'yozm':
                if post.get('content'):
                    summary = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
                    message += f"**요약:** {summary}\n"
            elif post_type == 'news':
                if post.get('time'):
                    message += f"**시간:** {post['time']}\n"
            message += f"**링크:** {post['link']}\n\n"
        
        print("메시지 전송 시도 중...")
        await channel.send(message)
        print(f"{type_names[post_type]} 메시지 전송 완료")
    except discord.errors.Forbidden:
        print(f"오류: 채널에 메시지를 보낼 권한이 없습니다. 채널: {channel.name}")
    except discord.errors.HTTPException as e:
        print(f"오류: HTTP 예외 발생: {str(e)}")
    except Exception as e:
        print(f"메시지 전송 중 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc())

async def check_and_send_posts(post_type, get_posts_func, channel_id):
    global last_run_times, last_post_ids
    
    now = datetime.now()
    last_run = last_run_times.get(post_type)
    
    print(f"\n=== {type_names[post_type]} 체크 시작 ===")
    print(f"채널 ID: {channel_id}")
    print(f"마지막 실행 시간: {last_run}")
    
    # 마지막 실행 시간이 없거나, 마지막 실행이 어제 이전인 경우에만 실행
    if last_run is None or (now.date() > last_run.date()):
        try:
            # 크롤링 실행
            print(f"{type_names[post_type]} 크롤링 시작...")
            posts = get_posts_func()
            
            if not posts:
                print(f"새로운 {type_names[post_type]}이(가) 없습니다.")
                return
                
            # 채널 확인
            channel = bot.get_channel(int(channel_id))
            if not channel:
                print(f"오류: 채널을 찾을 수 없습니다. 채널 ID: {channel_id}")
                return
                
            print(f"채널 정보: {channel.name} (ID: {channel.id})")
            
            # 새로운 게시물 확인 및 전송
            if last_post_ids[post_type] is None:
                # 최초 실행시 모든 게시물 전송
                print(f"최초 실행: {type_names[post_type]} 전송")
                await send_posts_to_channel(posts, channel, post_type)
                last_post_ids[post_type] = posts[0].get('id', '')
            else:
                # 새로운 게시물만 전송
                new_posts = []
                for post in posts:
                    if post.get('id', '') == last_post_ids[post_type]:
                        break
                    new_posts.append(post)
                
                if new_posts:
                    print(f"새로운 {type_names[post_type]} {len(new_posts)}개 발견")
                    await send_posts_to_channel(new_posts, channel, post_type)
                    last_post_ids[post_type] = new_posts[0].get('id', '')
                else:
                    print(f"새로운 {type_names[post_type]}이(가) 없습니다.")
            
            # 실행 시간 업데이트
            last_run_times[post_type] = now
            print(f"{type_names[post_type]} 체크 완료")
            
        except Exception as e:
            print(f"{type_names[post_type]} 체크 중 오류 발생: {str(e)}")
            import traceback
            print("상세 오류 정보:")
            print(traceback.format_exc())
    else:
        print(f"{type_names[post_type]} 크롤링은 하루에 한 번만 실행됩니다.")
        print(f"다음 실행 시간: {(last_run + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')}")

@bot.event
async def on_ready():
    print(f"{bot.user} 봇이 실행되었습니다!")
    print("디버그 모드로 실행 중...")
    
    try:
        # 초기 크롤링 실행
        print("\n=== 초기 크롤링 시작 ===")
        
        # QnA 크롤링
        qna_channel_id = CHANNEL_CONFIG['channels']['qna']['id']
        if qna_channel_id:
            await check_and_send_posts('qna', get_qna_posts, qna_channel_id)
            print("질문답변 크롤링 완료")
        
        # 뉴스 크롤링
        news_channel_id = CHANNEL_CONFIG['channels']['news']['id']
        if news_channel_id:
            await check_and_send_posts('news', get_news_posts, news_channel_id)
            print("뉴스 크롤링 완료")
        
        # 요즘IT 크롤링
        yozm_channel_id = CHANNEL_CONFIG['channels']['yozm']['id']
        if yozm_channel_id:
            await check_and_send_posts('yozm', get_yozm_posts, yozm_channel_id)
            print("요즘IT 크롤링 완료")
            
        print("=== 초기 크롤링 완료 ===")
        
        # 크롤링 완료 후 봇 종료
        print("크롤링이 완료되어 봇을 종료합니다.")
        await bot.close()
        
    except Exception as e:
        print(f"초기 크롤링 중 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc())
        await bot.close()

@bot.event
async def on_disconnect():
    print("디스코드 연결이 끊어졌습니다. 재연결을 시도합니다...")
    await asyncio.sleep(5)  # 재연결 전 잠시 대기
    
    try:
        if not bot.is_ready():
            print("봇이 준비되지 않았습니다. 재연결을 시도합니다...")
            await bot.connect(reconnect=True)
            print("재연결 시도 완료")
        else:
            print("봇이 이미 연결되어 있습니다.")
    except Exception as e:
        print(f"재연결 시도 중 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc())

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"오류 발생: {event}")
    print(f"인자: {args}")
    print(f"키워드 인자: {kwargs}")
    
    if event == 'on_ready':
        print("on_ready 이벤트에서 오류가 발생했습니다. 재연결을 시도합니다.")
        await asyncio.sleep(5)
        try:
            if not bot.is_ready():
                await bot.connect(reconnect=True)
                print("재연결 시도 완료")
        except Exception as e:
            print(f"재연결 시도 중 오류 발생: {str(e)}")
            import traceback
            print("상세 오류 정보:")
            print(traceback.format_exc())

@tasks.loop(time=dt_time(9, 0))  # 매일 오전 9시에 실행
async def check_qna():
    qna_channel_id = CHANNEL_CONFIG['channels']['qna']['id']
    if qna_channel_id:
        await check_and_send_posts('qna', get_qna_posts, qna_channel_id)

@tasks.loop(time=dt_time(10, 0))  # 매일 오전 10시에 실행
async def check_news():
    news_channel_id = CHANNEL_CONFIG['channels']['news']['id']
    if news_channel_id:
        await check_and_send_posts('news', get_news_posts, news_channel_id)

@tasks.loop(time=dt_time(11, 0))  # 매일 오전 11시에 실행
async def check_yozm():
    yozm_channel_id = CHANNEL_CONFIG['channels']['yozm']['id']
    if yozm_channel_id:
        await check_and_send_posts('yozm', get_yozm_posts, yozm_channel_id)

# 봇 실행 함수 수정
async def run_bot():
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            print(f"연결 시도 {retry_count + 1}/{max_retries}")
            
            # 이전 세션 정리
            if bot.is_ready():
                await bot.close()
                await asyncio.sleep(1)
            
            # 새로운 세션으로 시작
            await bot.start(os.getenv('DISCORD_TOKEN'))
            break
            
        except Exception as e:
            print(f"연결 시도 {retry_count + 1} 실패: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"5초 후 재시도합니다...")
                await asyncio.sleep(5)
            else:
                print("최대 재시도 횟수를 초과했습니다.")
                raise

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("봇이 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {str(e)}")
        import traceback
        print("상세 오류 정보:")
        print(traceback.format_exc()) 