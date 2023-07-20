from pathlib import Path

from mdboy import MarkdownManager
from mdboy.plugins import Tag

class TestMarkdownManager:
    def setup_method(self):
        self.manager = MarkdownManager(Path('.'))
        self.tag_plugin = Tag()
        self.manager.add_plugin(self.tag_plugin)

    def teardown_method(self):
        self.manager = None

    def test_add_dir(self):
        self.manager.add_dir('test')
        # order is not guaranteed
        set(self.manager.all_files) == set([Path('test/test.md')])

    def test_valid_commands(self):
        # order is not guaranteed
        assert set(self.tag_plugin.commands) == set(['add_tag', 'add_tags', 'remove_tag', 'remove_tags'])