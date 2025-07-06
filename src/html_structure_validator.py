#!/usr/bin/env python3
"""
HTML 구조 검증 및 자동 적응 시스템
"""

import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTMLStructureValidator:
    def __init__(self, config_file: str = 'html_patterns.json'):
        self.config_file = config_file
        self.patterns = self.load_patterns()
        
    def load_patterns(self) -> Dict:
        """저장된 HTML 패턴 로드"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'qna': {
                'selectors': [],
                'patterns': [],
                'last_updated': None
            },
            'news': {
                'selectors': [],
                'patterns': [],
                'last_updated': None
            }
        }
    
    def save_patterns(self):
        """HTML 패턴 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
    
    def analyze_html_structure(self, html: str, content_type: str) -> Dict:
        """HTML 구조 분석 및 패턴 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        analysis = {
            'selectors': [],
            'patterns': [],
            'items_found': 0
        }
        
        if content_type == 'qna':
            # Q&A 패턴 분석
            patterns = [
                # onclick 패턴
                {
                    'name': 'onclick_viewDetail',
                    'finder': lambda: soup.find_all(attrs={'onclick': re.compile(r'viewDetail')}),
                    'extractor': self._extract_qna_from_onclick
                },
                # 링크 패턴
                {
                    'name': 'link_ab2110',
                    'finder': lambda: soup.find_all('a', href=re.compile(r'ab-2110-\d+')),
                    'extractor': self._extract_qna_from_link
                },
                # 클래스 기반 패턴
                {
                    'name': 'class_article',
                    'finder': lambda: soup.select('div.article'),
                    'extractor': self._extract_qna_from_article
                },
                {
                    'name': 'class_qna_item',
                    'finder': lambda: soup.select('div.qna-item, div.question-item, li.qna'),
                    'extractor': self._extract_qna_from_article
                }
            ]
        else:  # news
            patterns = [
                # 뉴스 링크 패턴
                {
                    'name': 'link_ab2877',
                    'finder': lambda: soup.find_all('a', href=re.compile(r'ab-2877-\d+')),
                    'extractor': self._extract_news_from_link
                },
                {
                    'name': 'onclick_location',
                    'finder': lambda: soup.find_all(attrs={'onclick': re.compile(r'location\.href.*ab-2877')}),
                    'extractor': self._extract_news_from_onclick
                },
                {
                    'name': 'class_news_item',
                    'finder': lambda: soup.select('div.news-item, div.article-item, li.news'),
                    'extractor': self._extract_news_from_article
                }
            ]
        
        # 각 패턴 테스트
        for pattern in patterns:
            try:
                items = pattern['finder']()
                if items:
                    logger.info(f"패턴 '{pattern['name']}' 발견: {len(items)}개 항목")
                    analysis['patterns'].append({
                        'name': pattern['name'],
                        'count': len(items),
                        'sample': pattern['extractor'](items[0]) if items else None
                    })
                    if len(items) > analysis['items_found']:
                        analysis['items_found'] = len(items)
                        analysis['best_pattern'] = pattern['name']
            except Exception as e:
                logger.error(f"패턴 '{pattern['name']}' 분석 실패: {str(e)}")
        
        return analysis
    
    def _extract_qna_from_onclick(self, element) -> Dict:
        """onclick 속성에서 Q&A 정보 추출"""
        onclick = element.get('onclick', '')
        match = re.search(r'viewDetail\([\'"](\d+)[\'"]', onclick)
        post_id = match.group(1) if match else None
        
        title = element.get_text(strip=True)
        return {
            'id': post_id,
            'title': title[:100],
            'link': f"https://www.i-boss.co.kr/ab-2110-{post_id}" if post_id else None
        }
    
    def _extract_qna_from_link(self, element) -> Dict:
        """링크에서 Q&A 정보 추출"""
        href = element.get('href', '')
        match = re.search(r'ab-2110-(\d+)', href)
        post_id = match.group(1) if match else None
        
        return {
            'id': post_id,
            'title': element.get_text(strip=True)[:100],
            'link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
        }
    
    def _extract_qna_from_article(self, element) -> Dict:
        """article 요소에서 Q&A 정보 추출"""
        # 제목 찾기
        title_elem = element.select_one('a, h3, .title')
        title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)[:100]
        
        # 링크 찾기
        link_elem = element.select_one('a[href]')
        link = link_elem.get('href', '') if link_elem else ''
        
        # ID 추출
        post_id = None
        if link:
            match = re.search(r'ab-2110-(\d+)', link)
            post_id = match.group(1) if match else None
        
        return {
            'id': post_id,
            'title': title,
            'link': link if link.startswith('http') else f"https://www.i-boss.co.kr{link}" if link else None
        }
    
    def _extract_news_from_link(self, element) -> Dict:
        """링크에서 뉴스 정보 추출"""
        href = element.get('href', '')
        match = re.search(r'ab-2877-(\d+)', href)
        post_id = match.group(1) if match else None
        
        # href 앞에 슬래시 확인
        if not href.startswith('/') and not href.startswith('http'):
            href = '/' + href
        
        return {
            'id': post_id,
            'title': element.get_text(strip=True)[:100],
            'link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
        }
    
    def _extract_news_from_onclick(self, element) -> Dict:
        """onclick에서 뉴스 정보 추출"""
        onclick = element.get('onclick', '')
        match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick)
        href = match.group(1) if match else ''
        
        # ID 추출
        id_match = re.search(r'ab-2877-(\d+)', href)
        post_id = id_match.group(1) if id_match else None
        
        return {
            'id': post_id,
            'title': element.get_text(strip=True)[:100],
            'link': href if href.startswith('http') else f"https://www.i-boss.co.kr{href}"
        }
    
    def _extract_news_from_article(self, element) -> Dict:
        """article 요소에서 뉴스 정보 추출"""
        # 제목 찾기
        title_elem = element.select_one('a, h3, .title')
        title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)[:100]
        
        # 링크 찾기
        link_elem = element.select_one('a[href*="ab-2877"]')
        link = link_elem.get('href', '') if link_elem else ''
        
        # href 앞에 슬래시 확인
        if link and not link.startswith('/') and not link.startswith('http'):
            link = '/' + link
        
        # ID 추출
        post_id = None
        if link:
            match = re.search(r'ab-2877-(\d+)', link)
            post_id = match.group(1) if match else None
        
        return {
            'id': post_id,
            'title': title,
            'link': link if link.startswith('http') else f"https://www.i-boss.co.kr{link}" if link else None
        }
    
    def validate_and_update(self, html: str, content_type: str) -> Dict:
        """HTML 구조 검증 및 패턴 업데이트"""
        analysis = self.analyze_html_structure(html, content_type)
        
        result = {
            'valid': analysis['items_found'] > 0,
            'items_found': analysis['items_found'],
            'best_pattern': analysis.get('best_pattern'),
            'patterns': analysis['patterns'],
            'needs_update': False
        }
        
        # 저장된 패턴과 비교
        stored = self.patterns.get(content_type, {})
        if stored.get('best_pattern') != result['best_pattern']:
            result['needs_update'] = True
            logger.warning(f"{content_type} HTML 구조 변경 감지! 기존: {stored.get('best_pattern')}, 신규: {result['best_pattern']}")
        
        # 패턴 업데이트
        if result['valid'] and result['needs_update']:
            self.patterns[content_type] = {
                'best_pattern': result['best_pattern'],
                'patterns': result['patterns'],
                'last_updated': datetime.now().isoformat()
            }
            self.save_patterns()
            logger.info(f"{content_type} 패턴 업데이트 완료")
        
        return result

def create_adaptive_crawler(content_type: str, validator: HTMLStructureValidator):
    """적응형 크롤러 생성"""
    
    def adaptive_extract(soup: BeautifulSoup) -> List[Dict]:
        """HTML 구조에 적응하여 데이터 추출"""
        items = []
        
        # 저장된 최적 패턴 시도
        stored = validator.patterns.get(content_type, {})
        best_pattern = stored.get('best_pattern')
        
        if content_type == 'qna':
            if best_pattern == 'onclick_viewDetail':
                elements = soup.find_all(attrs={'onclick': re.compile(r'viewDetail')})
                for elem in elements:
                    items.append(validator._extract_qna_from_onclick(elem))
            elif best_pattern == 'link_ab2110':
                elements = soup.find_all('a', href=re.compile(r'ab-2110-\d+'))
                for elem in elements:
                    items.append(validator._extract_qna_from_link(elem))
            else:
                # 폴백: 모든 패턴 시도
                elements = soup.select('div.article') or soup.select('div.qna-item')
                for elem in elements:
                    items.append(validator._extract_qna_from_article(elem))
        
        else:  # news
            if best_pattern == 'link_ab2877':
                elements = soup.find_all('a', href=re.compile(r'ab-2877-\d+'))
                for elem in elements:
                    items.append(validator._extract_news_from_link(elem))
            elif best_pattern == 'onclick_location':
                elements = soup.find_all(attrs={'onclick': re.compile(r'location\.href.*ab-2877')})
                for elem in elements:
                    items.append(validator._extract_news_from_onclick(elem))
            else:
                # 폴백
                elements = soup.select('div.news-item') or soup.select('div.article-item')
                for elem in elements:
                    items.append(validator._extract_news_from_article(elem))
        
        # 유효한 항목만 필터링
        valid_items = [item for item in items if item.get('id') and item.get('link')]
        return valid_items
    
    return adaptive_extract