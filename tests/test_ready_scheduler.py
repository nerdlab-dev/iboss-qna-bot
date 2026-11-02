"""Exercise the actual ready handler with a real offline discord.py Loop."""
import ast
import asyncio
from contextlib import suppress
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from discord.ext import tasks


def load_ready(loop):
    source = Path(__file__).resolve().parents[1] / 'src' / 'iboss_qna_bot.py'
    module = ast.parse(source.read_text(encoding='utf-8'))
    ready = next(node for node in module.body
                 if isinstance(node, ast.AsyncFunctionDef) and node.name == 'on_ready')
    ready.decorator_list = []
    namespace = {'bot': SimpleNamespace(user='offline-test'), 'logger': Mock(),
                 'check_qna_task': loop}
    exec(compile(ast.Module(body=[ready], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['on_ready']


class ReadySchedulerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        @tasks.loop(hours=24)
        async def loop():
            pass
        self.loop = loop
        self.ready = load_ready(loop)

    async def asyncTearDown(self):
        await self.cancel_loop()

    async def cancel_loop(self):
        task = self.loop.get_task()
        self.loop.cancel()
        if task is not None:
            with suppress(asyncio.CancelledError):
                await task

    async def test_initial_ready_starts_scheduler(self):
        await self.ready()
        self.assertTrue(self.loop.is_running())

    async def test_repeated_ready_preserves_running_task(self):
        await self.ready()
        task = self.loop.get_task()
        for _ in range(3):
            await self.ready()
            self.assertIs(self.loop.get_task(), task)
            self.assertTrue(self.loop.is_running())

    async def test_ready_restarts_finished_task(self):
        await self.ready()
        previous = self.loop.get_task()
        await self.cancel_loop()
        self.assertFalse(self.loop.is_running())
        await self.ready()
        self.assertTrue(self.loop.is_running())
        self.assertIsNot(self.loop.get_task(), previous)


if __name__ == '__main__':
    unittest.main()
