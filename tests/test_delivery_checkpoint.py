"""Offline delivery/checkpoint regression tests; never import or start the bot."""
import ast
import asyncio
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

ROOT = Path(__file__).resolve().parents[1]


def load_function(path, name, namespace):
    # Execute the actual function without top-level Discord/Selenium/config effects.
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    function = next(node for node in tree.body
                    if isinstance(node, ast.AsyncFunctionDef) and node.name == name)
    function.decorator_list = []
    exec(compile(ast.Module(body=[function], type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


class DeliveryCheckpointTests(unittest.IsolatedAsyncioTestCase):
    def environment(self):
        channel = SimpleNamespace(name='offline', id=1, send=AsyncMock())
        posts = [{'id': 'new', 'title': 'Question', 'link': 'https://example.invalid/q'}]
        namespace = {
            'logger': Mock(),
            'CHANNEL_CONFIG': {'channels': {'qna': {'id': '1'}}},
            'bot': SimpleNamespace(user='offline', get_channel=Mock(return_value=channel),
                                   close=AsyncMock()),
            'load_last_posts': Mock(return_value=['old']),
            'save_last_posts': Mock(),
            'get_qna_posts': Mock(return_value=posts),
            'asyncio': SimpleNamespace(sleep=AsyncMock()),
            'datetime': datetime,
            'discord': SimpleNamespace(Embed=Mock(), Color=SimpleNamespace(blue=lambda: 0)),
        }
        namespace['send_qna_to_discord'] = load_function(
            'src/iboss_qna_bot.py', 'send_qna_to_discord', namespace)
        return namespace, channel, posts

    async def test_sender_reports_failure_and_success(self):
        env, channel, posts = self.environment()
        channel.send.side_effect = RuntimeError('offline send failed')
        self.assertIs(await env['send_qna_to_discord'](posts, channel), False)
        channel.send.side_effect = None
        self.assertIs(await env['send_qna_to_discord'](posts, channel), True)

    async def test_empty_sender_does_not_send(self):
        env, channel, _ = self.environment()
        self.assertIs(await env['send_qna_to_discord']([], channel), True)
        channel.send.assert_not_awaited()

    async def test_failed_delivery_keeps_checkpoint_in_both_entrypoints(self):
        for path, name in [('src/iboss_qna_bot.py', 'check_new_qna'),
                           ('src/run_once.py', 'on_ready')]:
            with self.subTest(path=path):
                env, channel, _ = self.environment()
                channel.send.side_effect = RuntimeError('offline send failed')
                run = load_function(path, name, env)
                await run()
                env['save_last_posts'].assert_not_called()
                # Since the old checkpoint survived, the next poll retries the question.
                channel.send.side_effect = None
                await run()
                self.assertEqual(channel.send.await_count, 2)
                env['save_last_posts'].assert_called_once_with(['new'])
                if name == 'on_ready':
                    self.assertEqual(env['bot'].close.await_count, 2)

    async def test_missing_channel_does_not_crawl_or_checkpoint(self):
        for path, name in [('src/iboss_qna_bot.py', 'check_new_qna'),
                           ('src/run_once.py', 'on_ready')]:
            with self.subTest(path=path):
                env, _, _ = self.environment()
                env['bot'].get_channel.return_value = None
                await load_function(path, name, env)()
                env['get_qna_posts'].assert_not_called()
                env['save_last_posts'].assert_not_called()
                if name == 'on_ready':
                    env['bot'].close.assert_awaited_once()

    async def test_empty_crawl_does_not_erase_checkpoint(self):
        for path, name in [('src/iboss_qna_bot.py', 'check_new_qna'),
                           ('src/run_once.py', 'on_ready')]:
            with self.subTest(path=path):
                env, channel, _ = self.environment()
                env['get_qna_posts'].return_value = []
                await load_function(path, name, env)()
                env['save_last_posts'].assert_not_called()
                channel.send.assert_not_awaited()

    async def test_unchanged_scheduled_posts_preserve_normal_checkpoint(self):
        env, channel, _ = self.environment()
        env['load_last_posts'].return_value = ['new']
        await load_function('src/iboss_qna_bot.py', 'check_new_qna', env)()
        channel.send.assert_not_awaited()
        env['save_last_posts'].assert_called_once_with(['new'])


if __name__ == '__main__':
    unittest.main()
