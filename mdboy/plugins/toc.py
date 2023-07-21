from pathlib import Path

from .plugin import MDFPlugin, command


class TableOfContents(MDFPlugin):
    """ Mixin for generating table of contents for markdown files."""
    def __init__(self):
        super().__init__()

    def find_toc(self, lines: list[str]) -> tuple[int, int]:
        """Find the line number of the table of contents.

        Args:
            path (Path): The path to the file to search.

        Returns:
            int: The line number of the table of contents.
        """

        toc_start = 0
        while toc_start < len(lines) and not lines[toc_start].startswith("# Table of Contents"):
            toc_start += 1

        toc_end = toc_start + 1
        while toc_end < len(lines) and not lines[toc_end].contains("---"):
            toc_end += 1

        return toc_start, toc_end
    
    def generate_toclist_from_lines(self, lines: list[str]) -> list[str]:
        """Generate a table of contents from a file with no table of contents.

        It uses # counts to determine the depth of the table of contents.
        """
        toclist: list[str, int] = []
        for line in lines:
            if line.startswith("#"):
                title = line.strip("#").strip()
                depth = title.count("#")
                toclist.append((title, depth))

        toc = ['# Table of Contents']
        for title, depth in toclist:
            toc.append(f"{' ' * depth}- {title}")
        toc.append("---")

        return toc

    @command(depends_on=["Title"])
    def modify_toc(self, lines: list[str]) -> list[str]:
        """Modify the table of contents.

        Args:
            lines (list[str]): The lines of the file to modify.
            idx (int): The line number of the table of contents.

        Returns:
            list[str]: The modified lines.
        """
        # Remove the old TOC
        toc_start, toc_end = self.find_toc(lines)
        if toc_start != len(lines):
            lines = lines[:toc_start] + lines[toc_end:]

        # Generate the new TOC
        toc = self.generate_toclist_from_lines(lines)

        # Add the new toc at the same position
        lines = lines[:toc_start] + toc + lines[toc_start:]

        return lines
    
    def hook(self, path: Path):
        with open(path, "r") as f:
            lines = f.readlines()

        lines = self.modify_toc(lines)
           
        with open(path, "w") as f:
            f.writelines(lines)

        return True
