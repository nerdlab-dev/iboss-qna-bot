"""Offline tests of actual handlers; never import/start Discord or Selenium."""
import ast
import asyncio
import logging
from pathlib import Path
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock


ROOT = Path(__file__).resolve().parents[1]


def load_handlers(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body
             if isinstance(node, ast.AsyncFunctionDef) and node.name in names]
    for node in nodes:
        node.decorator_list = []
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


class CrawlTests(unittest.IsolatedAsyncioTestCase):
    def namespace(self):
        return {
            "asyncio": asyncio,
            "logger": logging.getLogger("test"),
            "CHANNEL_CONFIG": {"channels": {"qna": {"id": "1"}}},
            "bot": SimpleNamespace(get_channel=lambda _: object()),
            "load_last_posts": lambda: [],
            "save_last_posts": lambda _: None,
            "send_qna_to_discord": AsyncMock(),
            "_qna_check_lock": asyncio.Lock(),
        }

    async def assert_responsive(self, path, names, entry, args=()):
        namespace = self.namespace()
        loop_thread = threading.get_ident()
        worker_threads = []
        released = threading.Event()
        entered = threading.Event()

        def crawl():
            worker_threads.append(threading.get_ident())
            entered.set()
            released.wait(0.2)
            return []

        namespace["get_qna_posts"] = crawl
        namespace["bot"] = SimpleNamespace(
            user="fixture", get_channel=lambda _: SimpleNamespace(name="fixture", id=1),
            close=AsyncMock(),
        )
        load_handlers(path, names, namespace)
        task = asyncio.create_task(namespace[entry](*args))
        # If the handler blocks, this coroutine resumes only after crawl returns.
        await asyncio.sleep(0.02)
        try:
            self.assertTrue(entered.is_set())
            self.assertFalse(task.done(), "event loop was blocked by the crawler")
            self.assertNotEqual(worker_threads, [loop_thread])
        finally:
            released.set()
            await task

    async def test_scheduled_and_manual_check_yields(self):
        await self.assert_responsive(
            ROOT / "src/iboss_qna_bot.py", {"check_new_qna", "_check_new_qna"}, "check_new_qna")

    async def test_test_command_yields(self):
        await self.assert_responsive(
            ROOT / "src/iboss_qna_bot.py", {"test_crawl"}, "test_crawl",
            (SimpleNamespace(send=AsyncMock()),))

    async def test_one_shot_yields(self):
        await self.assert_responsive(ROOT / "src/run_once.py", {"on_ready"}, "on_ready")

    async def test_checks_serialize_through_checkpoint(self):
        ns = self.namespace()
        stored = []
        ns["get_qna_posts"] = lambda: [{"id": "new"}]
        ns["load_last_posts"] = lambda: list(stored)
        ns["save_last_posts"] = lambda ids: stored.extend(ids)
        async def send(*_):
            await asyncio.sleep(0.01)
        ns["send_qna_to_discord"] = AsyncMock(side_effect=send)
        load_handlers(ROOT / "src/iboss_qna_bot.py", {"check_new_qna", "_check_new_qna"}, ns)
        await asyncio.gather(ns["check_new_qna"](), ns["check_new_qna"]())
        self.assertEqual(ns["send_qna_to_discord"].await_count, 1)

    async def test_failed_check_releases_lock(self):
        ns = self.namespace()
        def broken():
            raise RuntimeError("fixture failure")
        ns["get_qna_posts"] = broken
        load_handlers(ROOT / "src/iboss_qna_bot.py", {"check_new_qna", "_check_new_qna"}, ns)
        with self.assertRaises(RuntimeError):
            await ns["check_new_qna"]()
        ns["get_qna_posts"] = lambda: []
        await asyncio.wait_for(ns["check_new_qna"](), timeout=1)


if __name__ == "__main__":
    unittest.main()
