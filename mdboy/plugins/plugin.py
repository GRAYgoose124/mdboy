from abc import ABCMeta, abstractmethod
from pathlib import Path

LOWEST_PRIORITY = 100

def command(*args, **kwargs):
    """Decorator for defining commands,

    It should allow one to go
    @command(depends_on=["Title"], required_args=["arg"])
    """

    def func_wrapper(func):
        func.is_command = True
        func.depends_on = kwargs.get("depends_on", [])
        func.required_args = kwargs.get("required_args", [])
        return func

    return func_wrapper

class CommandProvider(type):
    """Metaclass for MDFPlugins that allows them to define commands by using @command decorator."""
    def __new__(cls, name, bases, attrs):
        attrs['_commands'] = {}
        for key, val in attrs.items():
            if hasattr(val, 'is_command'):
                attrs['_commands'][key] = val

        return super().__new__(cls, name, bases, attrs)


class CommandProviderMeta(CommandProvider, ABCMeta):
    pass

class MDFPlugin(metaclass=CommandProviderMeta):
    """Base class for markdown file plugins."""
    @property
    def commands(self):
        """ Returns a list of available commands from the plugin for the Markdown Manager to use. 


        A command takes lines of a file and returns modified lines of a file.
        """
        return self._commands

    # @abstractmethod
    # def hook(self, path: Path):
    #     """Hook for the MarkdownManager to call when it finds a file that matches the plugin."""
    #     pass
    
    def __hash__(self) -> int:
        return hash(self.__class__.__name__)
    
    def __eq__(self, o: object) -> bool:
        return self.__class__.__name__ == o.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} MDFPlugin"
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}"
    
