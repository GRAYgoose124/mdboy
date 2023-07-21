import logging

from pathlib import Path

from .plugins.plugin import MDFPlugin
from .plugins.manager import PluginManager
from .utils import flatten

l = logging.getLogger(__name__)

    
class MarkdownManager(PluginManager):
    def __init__(self, root: Path = None):
        super().__init__()
        self._root = root
        # These are dicts keyed by a Plugin class, with values being a list of paths.
        self._included_dirs: dict[MDFPlugin, list[Path]] = {'common': []}
        self._included_files: dict[MDFPlugin, list[Path]] = {'common': []}

    @property
    def root(self):
        """Get the root directory of the manager."""
        return self._root

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

    @property
    def all_dirs(self):
        """ All managed directories. """
        return list(flatten(self.all_files_by_dir.keys()))
    
    @property
    def included_dirs(self):
        """ All managed directories, grouped by plugin."""
        return self._included_dirs
    
    @property
    def all_files_by_plugin(self):
        """ All managed files, including common files, grouped by plugin."""
        files = {}

        for plugin in self.plugins:
            files[plugin] = self.active_files_for_plugin(plugin)

        return files

    def active_files_for_plugin(self, plugin: MDFPlugin):
        """All managed files that match a plugin, including common files."""
        files = [] 
        
        if plugin in self._included_dirs:
            for d in self._included_dirs[plugin]:
                files.extend(d.glob("**/*.md"))

        if plugin in self._included_files:
            files.extend(self._included_files[plugin])

        files.extend(self._included_files['common'])

        return files
    
    def run_plugins(self):
        """Run all plugins on all files."""
        for plugin in self.plugins:
            for file in self.active_files_for_plugin(plugin):
                plugin.hook(file)

    def execute(self, commands: list[tuple[MDFPlugin, str, list]] = None):
        """Execute given and pending commands on the manager."""
        if commands:
            self.queue_commands(commands)

        self.run_queued_commands()
        self.run_plugins()