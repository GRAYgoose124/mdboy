import logging
from pathlib import Path

from .plugin import MDFPlugin, command

l = logging.getLogger(__name__)


class TitleTags(MDFPlugin):
    """ Mixin for tagging markdown files deterministically."""
    def __init__(self, tags: list[str] = None):
        super().__init__()

    @command(depends_on=["Title"], required_args=["tags"])
    def add_tags(self, lines: list[str], tags: list[str]) -> list[str]:
        """Add tags to a the file.

        - It looks for a `# Arbitrary Title` line and adds the tags below it. 
            - If the tags already exist, it appends the new tags to the existing ones.

        Args:
            lines (list[str]): The lines of the file to modify.
            tags (list[str]): The tags to add.
        
        Returns:
            list[str]: The complete modified lines or empty list if no title was found.

        """
        idx = 0
        while idx < len(lines) and not lines[idx].strip().startswith("# "):
            idx += 1
        idx += 1

        if idx == len(lines):
            # no title found
            return []
        
        if self.tags > 1:
            tags_str = ", ".join([f"#{tag}" for tag in self.tags])
        else:
            tags_str = f"#{self.tags[0]}"

        taglist = lines[idx].strip()
        if taglist.startswith("["):
            # taglist already exists, append to it by removing the closing bracket and adding the tag and closing bracket.
            taglist = f"{taglist[:-1]}, {tags_str}]"
            lines[idx] = taglist
        else:
            # taglist does not exist, create it with the tag.
            lines.insert(idx, f"[{tags_str}]")


        return lines