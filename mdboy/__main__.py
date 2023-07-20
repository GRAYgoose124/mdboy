#!/usr/bin/env python3
import logging

from pathlib import Path

from . import MarkdownManager
from .plugins import Tag


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s|\t%(name)s| %(message)s")

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
    main()