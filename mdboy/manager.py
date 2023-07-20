import logging

from pathlib import Path

from .plugin import MDFPlugin
from .utils import flatten

l = logging.getLogger(__name__)

    
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