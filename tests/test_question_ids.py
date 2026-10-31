"""Offline crawler ID regressions; no bot imports, browser or network."""
import ast
from datetime import datetime
import logging
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'iboss_qna_bot.py'

def crawl(href, now, onclick=''):
    title = SimpleNamespace(text='Synthetic question', get=lambda key, default='': href)
    question = SimpleNamespace(
        select_one=lambda selector: title if selector == 'div.content a' else None,
        select=lambda selector: [],
        get=lambda key, default='': onclick if key == 'onclick' else default,
    )
    driver = Mock(page_source='<synthetic>')
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'get_qna_posts')
    scope = {
        'logger': logging.getLogger('offline'), 'get_chrome_driver': lambda: driver,
        'WebDriverWait': lambda *args: SimpleNamespace(until=lambda *args: None),
        'EC': SimpleNamespace(presence_of_element_located=lambda x: x),
        'By': SimpleNamespace(CSS_SELECTOR='css'), 'time': SimpleNamespace(sleep=lambda _: None),
        'BeautifulSoup': lambda *args: SimpleNamespace(select=lambda _: [question]),
        'datetime': SimpleNamespace(now=lambda: now), 're': re,
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), scope)
    posts = scope['get_qna_posts']()
    driver.quit.assert_called_once()
    return posts[0]

class QuestionIdTests(unittest.TestCase):
    def test_detail_board_id_is_stable_across_checks(self):
        # Checked-in crawler results use ab-2110 detail URLs, not listing board ab-2109.
        link = 'https://www.i-boss.co.kr/ab-2110-12345'
        first = crawl(link, datetime(2026, 10, 31, 9, 0))
        later = crawl(link, datetime(2026, 10, 31, 9, 1))
        self.assertEqual(first['id'], '12345')
        self.assertEqual(later['id'], first['id'])
        self.assertIn(later['id'], [first['id']])

    def test_root_relative_detail_and_query(self):
        post = crawl('/ab-2110-67890?view=1#answer', datetime(2026, 10, 31))
        self.assertEqual(post['id'], '67890')
        self.assertEqual(post['link'], 'https://www.i-boss.co.kr/ab-2110-67890?view=1#answer')

    def test_legacy_board_id_preserved(self):
        self.assertEqual(crawl('/ab-2109-12345', datetime(2026, 10, 31))['id'], '12345')

    def test_onclick_still_has_priority(self):
        self.assertEqual(crawl('/ab-2110-12345', datetime(2026, 10, 31), "viewDetail('existing-id')")['id'], 'existing-id')

    def test_unknown_or_missing_link_keeps_existing_fallback(self):
        for link in ['', '/unrelated', '/ab-9999-12345']:
            with self.subTest(link=link):
                self.assertEqual(crawl(link, datetime(2026, 10, 31, 9, 0))['id'], 'qna_1_202610310900')

if __name__ == '__main__':
    unittest.main()
