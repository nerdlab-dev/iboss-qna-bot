"""정기 루프의 시간 계산만 검사해요. 봇·크롤러·네트워크는 실행하지 않아요."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from discord.ext import tasks


def load_schedule():
    source = Path(__file__).resolve().parents[1] / 'src' / 'iboss_qna_bot.py'
    module = ast.parse(source.read_text(encoding='utf-8'))
    # 모듈 전체 import 시 Discord 클라이언트/파일 로깅이 생성되므로
    # datetime import와 실제 정기 루프 정의만 동일한 AST로 읽어요.
    nodes = [node for node in module.body
             if (isinstance(node, ast.ImportFrom) and node.module == 'datetime')
             or (isinstance(node, ast.AsyncFunctionDef) and node.name == 'check_qna_task')]
    namespace = {'tasks': tasks}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['check_qna_task']


class QnaScheduleTest(unittest.TestCase):
    def test_daily_time_is_explicitly_korean_morning(self):
        scheduled = load_schedule().time[0]
        self.assertEqual((scheduled.hour, scheduled.minute), (9, 0))
        self.assertEqual(scheduled.utcoffset(), timedelta(hours=9))

    def test_before_korean_morning_uses_next_utc_midnight(self):
        now = datetime(2026, 10, 29, 23, 59, tzinfo=timezone.utc)
        following = load_schedule()._get_next_sleep_time(now)
        self.assertEqual(following, datetime(2026, 10, 30, 0, 0, tzinfo=timezone.utc))

    def test_after_morning_waits_until_next_korean_day(self):
        now = datetime(2026, 10, 30, 0, 1, tzinfo=timezone.utc)
        following = load_schedule()._get_next_sleep_time(now)
        self.assertEqual(following, datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc))

    def test_korean_evening_does_not_schedule_another_run_same_day(self):
        now = datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc)
        following = load_schedule()._get_next_sleep_time(now)
        self.assertEqual(following, datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc))


if __name__ == '__main__':
    unittest.main()
