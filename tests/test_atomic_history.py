"""Offline tests of the real history functions without importing/starting the bot."""
import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'iboss_qna_bot.py'

class AtomicHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'last_qna_posts.json'
        self.path.write_text('["previous"]', encoding='utf-8')
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in {'save_last_posts', 'load_last_posts'}]
        self.ns = {'os': os, 'json': json, 'tempfile': tempfile, 'LAST_POST_FILE': str(self.path)}
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), self.ns)

    def assert_preserved(self):
        self.assertEqual(self.ns['load_last_posts'](), ['previous'])
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.path])

    def test_success_replaces_complete_history(self):
        self.ns['save_last_posts'](['new', 'second'])
        self.assertEqual(self.ns['load_last_posts'](), ['new', 'second'])
        self.assertEqual(list(Path(self.temp.name).iterdir()), [self.path])

    def test_partial_write_failure_preserves_previous_history(self):
        def fail_after_partial_write(value, handle):
            handle.write('["partial')
            raise OSError('simulated disk write failure')
        with patch.object(json, 'dump', side_effect=fail_after_partial_write):
            with self.assertRaises(OSError):
                self.ns['save_last_posts'](['new'])
        self.assert_preserved()

    def test_serialization_failure_preserves_previous_history(self):
        with self.assertRaises(TypeError):
            self.ns['save_last_posts']([object()])
        self.assert_preserved()

    def test_replace_failure_preserves_previous_history(self):
        with patch.object(os, 'replace', side_effect=OSError('simulated replace failure')):
            with self.assertRaises(OSError):
                self.ns['save_last_posts'](['new'])
        self.assert_preserved()

    def test_first_save_and_empty_history(self):
        self.path.unlink()
        self.ns['save_last_posts']([])
        self.assertEqual(self.ns['load_last_posts'](), [])

    def test_replacement_is_same_directory_and_closed_complete_file(self):
        replace = os.replace
        def inspect_replace(source, destination):
            self.assertEqual(Path(source).parent, self.path.parent)
            self.assertEqual(json.loads(Path(source).read_text()), ['new'])
            self.assertEqual(self.ns['load_last_posts'](), ['previous'])
            replace(source, destination)
        with patch.object(os, 'replace', side_effect=inspect_replace) as replacement:
            self.ns['save_last_posts'](['new'])
        replacement.assert_called_once()
        self.assertEqual(self.ns['load_last_posts'](), ['new'])

if __name__ == '__main__':
    unittest.main()
