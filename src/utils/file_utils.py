from pathlib import Path
from typing import Optional


def sanitize_path(file_path: Path, project_root: Optional[Path] = None) -> str:
    """
    Sanitize a file path for LLM and reporting.
    If project_root is provided, returns path relative to project root.
    Otherwise, returns just the filename.
    """
    if project_root:
        try:
            return str(file_path.relative_to(project_root))
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