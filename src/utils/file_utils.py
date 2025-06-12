from pathlib import Path
from typing import Optional
import os

# Windows-specific path handling
if os.name == 'nt':  # Check if running on Windows
    def normalize_windows_path(path: str) -> str:
        """Convert Windows path to forward slashes and handle drive letters."""
        # Remove drive letter if present (e.g., C:)
        if ':' in path:
            path = path.split(':', 1)[1]
        # Convert backslashes to forward slashes
        return path.replace('\\', '/').lstrip('/')

def sanitize_path(file_path: Path, project_root: Optional[Path] = None) -> str:
    """
    Sanitize a file path for LLM and reporting.
    If project_root is provided, returns path relative to project root.
    Otherwise, returns just the filename.
    Normalizes path separators to forward slashes for consistency.
    """
    if project_root:
        try:
            # Convert to relative path and normalize separators
            rel_path = str(file_path.relative_to(project_root))
            if os.name == 'nt':  # Windows-specific handling
                return normalize_windows_path(rel_path)
            return rel_path
        except ValueError:
            # If file is not under project root, return just the filename
            return file_path.name
    return file_path.name


def get_project_root(file_path: Path) -> Optional[Path]:
    """
    Try to determine the project root directory.
    Looks for common project root indicators like pom.xml, build.gradle, etc.
    """
    current = file_path
    while current != current.parent:
        if any((current / marker).exists() for marker in ['pom.xml', 'build.gradle', '.git', 'src']):
            return current
        current = current.parent
    return None 