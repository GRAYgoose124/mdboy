from pathlib import Path

from ..plugin import MDFPlugin, command


class Tag(MDFPlugin):
    """ Mixin for tagging markdown files deterministically."""
    def __init__(self, tags: list[str] = None):
        super().__init__()
        self._tags = tags or []

    @property
    def tags(self):
        return self._tags

    @command
    def add_tag(self, tag: str):
        self._tags.append(tag)

    @command
    def add_tags(self, tags: list[str]):
        self._tags.extend(tags)
    
    @command
    def remove_tag(self, tag: str):
        self._tags.remove(tag)

    @command
    def remove_tags(self, tags: list[str]):
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