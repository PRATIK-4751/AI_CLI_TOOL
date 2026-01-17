from pathlib import Path


class FileToolError(Exception):
    """Custom exception for file tool errors."""
    pass


class FileTools:
    """
    Safe file system operations scoped to a root directory.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()

        if not self.root_dir.exists():
            raise FileToolError("Root directory does not exist")

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a path safely within the root directory.
        Prevents directory traversal.
        """
        path = (self.root_dir / relative_path).resolve()

        if not str(path).startswith(str(self.root_dir)):
            raise FileToolError("Access outside working directory is not allowed")

        return path

    def read_file(self, relative_path: str) -> str:
        """
        Read and return file contents.
        """
        path = self._resolve_path(relative_path)

        if not path.exists():
            raise FileToolError(f"File not found: {relative_path}")

        if not path.is_file():
            raise FileToolError(f"Not a file: {relative_path}")

        return path.read_text(encoding="utf-8")

    def write_file(
        self,
        relative_path: str,
        content: str,
        overwrite: bool = False,
    ):
        """
        Write content to a file.

        By default, will NOT overwrite existing files.
        """
        path = self._resolve_path(relative_path)

        if path.exists() and not overwrite:
            raise FileToolError(
                f"File already exists: {relative_path}. "
                "Set overwrite=True to overwrite."
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists.
        """
        try:
            path = self._resolve_path(relative_path)
            return path.exists()
        except FileToolError:
            return False
