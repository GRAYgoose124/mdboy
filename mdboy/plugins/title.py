import logging

from .plugin import MDFPlugin, command
from pathlib import Path


l = logging.getLogger(__name__)

class Title(MDFPlugin):
    """ Mixin for tagging markdown files deterministically."""
    def __init__(self):
        super().__init__()

    def find_title(self, lines: list[str]) -> int:
        """Find the line number of the table of contents.

        Args:
            path (Path): The path to the file to search.

        Returns:
            int: The line number of the table of contents.
        """

        title_start = 0
        while title_start < len(lines) and not lines[title_start].strip().startswith("# "):
            title_start += 1

        return title_start


    @command(required_args=["title"])
    def modify_title(self, lines: list[str], title: str) -> list[str]:
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

        idx = self.find_title(lines)

        if idx == len(lines):
            # no title found
            l.info(f"No title found, adding title to top of file.")
            lines.insert(0, f"# {title}\n")
        else:
            # title found, modify it
            l.info(f"Title found, modifying it.")
            lines[idx] = f"# {title}\n"

        return lines