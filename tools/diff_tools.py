import difflib
from pathlib import Path


class DiffTools:
    """
    Utilities for generating and applying diffs safely.
    """

    @staticmethod
    def generate_diff(
        original: str,
        modified: str,
        filename: str = "file",
    ) -> str:
        """
        Generate a unified diff between original and modified text.
        """

        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )

        return "".join(diff)
