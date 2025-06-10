import os
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.core.config import settings
from src.core.models import JavaFile


class FileAnalyzer:
    """Analyzes Java files in a project."""

    def analyze_project(self, project_path: Path) -> List[JavaFile]:
        """Analyze all Java files in the project."""
        logger.info(f"Starting analysis of project at {project_path}")
        
        java_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if not self._should_analyze_file(file):
                    continue
                
                file_path = Path(root) / file
                if not self._is_within_size_limit(file_path):
                    logger.warning(f"Skipping {file_path}: exceeds size limit")
                    continue
                
                try:
                    java_file = self._analyze_file(file_path)
                    if java_file:
                        java_files.append(java_file)
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {str(e)}")
        
        logger.info(f"Analysis complete. Found {len(java_files)} Java files")
        return java_files

    def _should_analyze_file(self, filename: str) -> bool:
        """Check if a file should be analyzed."""
        # Check file extension
        if not any(filename.endswith(ext) for ext in settings.SUPPORTED_EXTENSIONS):
            return False
        
        # Check exclude patterns
        if any(pattern in filename for pattern in settings.EXCLUDE_PATTERNS):
            return False
        
        return True

    def _is_within_size_limit(self, file_path: Path) -> bool:
        """Check if file size is within limits."""
        try:
            return file_path.stat().st_size <= settings.MAX_FILE_SIZE
        except OSError:
            return False

    def _analyze_file(self, file_path: Path) -> Optional[JavaFile]:
        """Analyze a single Java file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract package name
            package = self._extract_package(content)
            
            # Determine file type
            file_type = self._determine_file_type(content)
            
            return JavaFile(
                path=file_path,
                content=content,
                package=package,
                file_type=file_type
            )
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return None

    def _extract_package(self, content: str) -> str:
        """Extract package name from Java file content."""
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('package '):
                return line[8:].rstrip(';')
        return ""

    def _determine_file_type(self, content: str) -> str:
        """Determine the type of Java file."""
        content_lower = content.lower()
        
        if 'interface ' in content_lower:
            return 'interface'
        elif 'enum ' in content_lower:
            return 'enum'
        elif 'class ' in content_lower:
            return 'class'
        else:
            return 'unknown' 