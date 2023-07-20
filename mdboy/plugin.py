from abc import ABCMeta, abstractmethod
from pathlib import Path


def command(func):
    """Decorator for defining commands."""
    func.is_command = True
    return func

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
    
