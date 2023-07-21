from .plugin import MDFPlugin

class PluginManager:
    def __init__(self) -> None:
        self.plugins: list[MDFPlugin] = []
        self._last_plugins_hash = "None"

        self._valid_commands: list[str] = []
        self._queued_commands: list[tuple[MDFPlugin, str, list]] = []
    
    def add_plugin(self, plugin: MDFPlugin):
        """Add a plugin to the manager."""
        self.plugins.append(plugin)

    def add_plugins(self, *plugins: MDFPlugin):
        """Add plugins to the manager."""
        for plugin in plugins:
            self.add_plugin(plugin)

    def remove_plugin(self, plugin: MDFPlugin):
        """Remove a plugin from the manager."""
        self.plugins.remove(plugin)

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
            func = getattr(plugin, cmd)
            required = func.required_args
            if len(args) < len(required):
                l.error(f"Command {cmd} requires {len(required)} arguments, {len(args)} given.")
            
            result = func(*args)
            l.debug(f"Ran command {cmd} with args {args} on plugin {plugin}. Result: {result}")

        self._queued_commands.clear()

    def fill_command_dependencies(self):
        pass

    