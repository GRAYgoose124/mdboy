#!/usr/bin/env python3
from abc import ABC, ABCMeta, abstractmethod
import logging
import unittest
import click

from pathlib import Path


l = logging.getLogger(__name__)

    
class CommandProvider(type):
    """Metaclass for MDFPlugins that allows them to define commands by prefixing methods with `cmd_`."""
    def __new__(cls, name, bases, attrs):
        attrs['_commands'] = {}
        for key, val in attrs.items():
            if key.startswith('cmd_'):
                attrs['_commands'][key[4:]] = val


    
        return super().__new__(cls, name, bases, attrs)


class CommandProviderMeta(CommandProvider, ABCMeta):
    pass

class MDFPlugin(metaclass=CommandProviderMeta):
    """Base class for markdown file plugins."""
    @property
    def commands(self):
        return self._commands

    @abstractmethod
    def hook(self, path: Path):
        """Hook for the MarkdownManager to call when it finds a file that matches the plugin."""
        pass
    
    def __hash__(self) -> int:
        return hash(self.__class__.__name__)
    
    def __eq__(self, o: object) -> bool:
        return self.__class__.__name__ == o.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} MDFPlugin"
    

class Tag(MDFPlugin):
    """ Mixin for tagging markdown files deterministically."""
    def __init__(self, tags: list[str] = None):
        super().__init__()
        self._tags = tags or []

    @property
    def tags(self):
        return self._tags

    def cmd_add_tag(self, tag: str):
        self._tags.append(tag)

    def cmd_add_tags(self, tags: list[str]):
        self._tags.extend(tags)
    
    def cmd_remove_tag(self, tag: str):
        self._tags.remove(tag)

    def cmd_remove_tags(self, tags: list[str]):
        for tag in tags:
            self.remove_tag(tag)

    def hook(self, path: Path):
        """Add tags to a the file.

        - It looks for a `# Arbitrary Title` line and adds the tags below it. 
            - If the tags already exist, it appends the new tags to the existing ones.

        Args:
            file (Path): The file to add tags to.
            tags (list[str]): The tags to add.

        Example:
            ```py
            add_tags_to_file("README.md", ["tag1", "tag2", "tag3"])
            ```

            Assuming a valid input markdown, produces:
            
            ```md
            # Readme
            [#tag1, #tag2, #tag3, ...]
            ```

        Returns:
            bool: True if the file was modified, False otherwise.
        """
        if not self.tags:
            l.info(f"No tags to add, prematurely returning.")
            return
        
        with open(path, "r") as f:
            lines = f.readlines()

        idx = 0
        while idx < len(lines) and not lines[idx].strip().startswith("# "):
            idx += 1
        idx += 1

        if idx == len(lines):
            # no title found
            return False
        
        if self.tags > 1:
            tags_str = ", ".join([f"#{tag}" for tag in self.tags])
        else:
            tags_str = f"#{self.tags[0]}"

        taglist = lines[idx].strip()
        if taglist.startswith("["):
            # taglist already exists, append to it by removing the closing bracket and adding the tag and closing bracket.

            taglist = f"{taglist[:-1]}, #{tags_str}]"
            lines[idx] = taglist
        else:
            # taglist does not exist, create it with the tag.
            lines.insert(idx, f"[#{tags_str}]")

        with open(path, "w") as f:
            f.writelines(lines)

        return True


def flatten(container):
    """ From https://stackoverflow.com/a/10824420 """
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i

class MarkdownManager:
    def __init__(self, root: Path = None):
        self._root = root
        # These are dicts keyed by a Plugin class, with values being a list of paths.
        self._included_dirs: dict[MDFPlugin, list[Path]] = {'common': []}
        self._included_files: dict[MDFPlugin, list[Path]] = {'common': []}

        self.plugins: list[MDFPlugin] = []
        self._last_plugins_hash = "None"
        self._valid_commands: list[str] = []
        self._queued_commands: list[tuple[MDFPlugin, str, list]] = []

    @property
    def root(self):
        """Get the root directory of the manager."""
        return self._root

    def add_plugin(self, plugin: MDFPlugin):
        """Add a plugin to the manager."""
        self.plugins.append(plugin)

    def remove_plugin(self, plugin: MDFPlugin):
        """Remove a plugin from the manager."""
        self.plugins.remove(plugin)

    def add_dir(self, path: Path, plugin: MDFPlugin = None):
        """Add a directory to the manager."""
        if self.root:
            path = self.root / path
        elif not isinstance(path, Path):
            path = Path(path)

        if not path.is_dir():
            l.warning(f"{path} is not a directory.")

        if plugin:
            self._included_dirs[plugin].setdefault(path, []).append(path)
        else:
            self._included_dirs['common'].append(path)

    def add_file(self, path: Path, plugin: MDFPlugin = None):
        """Add a file to the manager."""
        if self.root:
            path = self.root / path
        elif not isinstance(path, Path):
            path = Path(path)

        if not path.is_file():
            l.warning(f"{path} is not a file.")

        if plugin:
            self._included_files[plugin].setdefault(path, []).append(path)
        else:
            self._included_files['common'].setdefault(path, []).append(path)

    @property
    def all_files(self):
        """All managed files, including common files."""
        return list(flatten(self.all_files_by_dir.values()))
    
    @property
    def all_files_by_dir(self):
        """All managed files, including common files, grouped by directory."""
        files = {}

        
        for dirs in self._included_dirs.values():
            for d in dirs:
                files.setdefault(d, []).extend(d.glob("*.md"))

        for paths in self._included_files.values():
            for path in paths:
                files.setdefault(path.parent, []).append(path)

        return files
    
    def plugin_files(self, plugin: MDFPlugin):
        """All managed files that match a plugin, including common files."""
        files = [] 
        
        if plugin in self._included_dirs:
            for d in self._included_dirs[plugin]:
                files.extend(d.glob("**/*.md"))

        if plugin in self._included_files:
            files.extend(self._included_files[plugin])

        files.extend(self._included_files['common'])

        return files

    @property
    def all_files_by_plugin(self):
        """ All managed files, including common files, grouped by plugin."""
        files = {}

        for plugin in self.plugins:
            files[plugin] = self.plugin_files(plugin)

        return files

    @property
    def all_dirs(self):
        """ All managed directories. """
        return list(flatten(self.all_files_by_dir.keys()))
    
    @property
    def included_dirs(self):
        """ All managed directories, grouped by plugin."""
        return self._included_dirs
    
    @property
    def valid_commands(self):
        """ All valid commands for the manager."""

        plugins_hash = sum([hash(plugin) for plugin in self.plugins])
        if self._last_plugins_hash != plugins_hash:
            for plugin in self.plugins: 
                self._valid_commands.extend(plugin.commands.keys())
            self._last_plugins_hash = plugins_hash

        return self._valid_commands
    
    @property
    def queued_commands(self):
        """ All commands queued to run on the manager. """
        return self._queued_commands

    def queue_command(self, plugin: MDFPlugin, cmd: str, args: list):
        """Queue a command to run on the manager."""
        if plugin not in self.plugins:
            l.error(f"Plugin {plugin} is not in the manager.")
        elif not hasattr(plugin, cmd):
            l.error(f"Plugin {plugin} has no command {cmd}.")
        else:
            self._queued_commands.append((plugin, cmd, args))

    def queue_commands(self, commands: list[tuple[MDFPlugin, str, list]]):
        """Queue commands to run on the manager."""
        for plugin, cmd, args in commands:
            self.queue_command(plugin, cmd, args)

    def remove_queued_command(self, plugin: MDFPlugin, cmd: str, args: list):
        """Remove a queued command from the manager."""
        self._queued_commands.remove((plugin, cmd, args))

    def run_queued_commands(self):
        """Run all queued commands on the manager."""
        for plugin, cmd, args in self._queued_commands:
            getattr(plugin, cmd)(*args)

        self._queued_commands.clear()

    def run_plugins(self):
        """Run all plugins on all files."""
        for plugin in self.plugins:
            for file in self.plugin_files(plugin):
                plugin.hook(file)

    def run(self):
        """Run all plugins and commands on the manager."""
        self.run_queued_commands()
        self.run_plugins()

    def execute(self, commands: list[tuple[MDFPlugin, str, list]] = None):
        """Execute given and pending commands on the manager."""
        if commands:
            self.queue_commands(commands)

        self.run()


class TestMarkdownManager(unittest.TestCase):
    def setUp(self):
        self.manager = MarkdownManager(Path('.'))
        self.manager.add_plugin(Tag())

    def test_add_dir(self):
        self.manager.add_dir('test')
        self.assertEqual(self.manager.all_files, [Path('test/test.md')])


def test_main():
    unittest.main()


def main():
    logging.basicConfig(level=logging.DEBUG)
    l.setFormatter(logging.Formatter("%(levelname)s|\t%(name)s| %(message)s"))

    manager = MarkdownManager(Path('.'))
    manager.add_plugin(Tag())

    while True:
        try:
            cmd = input(">>> ")
        except KeyboardInterrupt:
            print()
            return
        
        if cmd == "exit":
            break
        else:
            try:
                manager.execute(cmd)
            except Exception as e:
                l.error(f"Exception raised while executing command: {e}")
                print(f"Valid commands are: {manager.valid_commands}")



if __name__ == '__main__':
    print("Running tests...")
    test_main()
    print("Tests complete.")
    main()