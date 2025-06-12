import os
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.core.config import settings
from src.core.models import JavaFile, FileImportance


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
            
            # Calculate importance scores
            importance = self._calculate_file_importance(file_path, content, file_type)
            
            return JavaFile(
                path=file_path,
                content=content,
                package=package,
                file_type=file_type,
                importance=importance
            )
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return None

    def _calculate_file_importance(self, file_path: Path, content: str, file_type: str) -> FileImportance:
        """Calculate importance scores for a Java file."""
        importance = FileImportance()
        
        # Check for main class
        importance.is_main_class = self._is_main_class(content)
        
        # Check for entry point
        importance.is_entry_point = self._is_entry_point(content)
        
        # Check for config file
        importance.is_config_file = self._is_config_file(content, file_type)
        
        # Calculate complexity score
        importance.complexity_score = self._calculate_complexity_score(content)
        
        # Calculate dependency score
        importance.dependency_score = self._calculate_dependency_score(content)
        
        # Calculate business logic score
        importance.business_logic_score = self._calculate_business_logic_score(content)
        
        # Calculate total score
        importance.calculate_total_score()
        
        return importance

    def _is_main_class(self, content: str) -> bool:
        """Check if the file contains a main class."""
        return 'public static void main(' in content

    def _is_entry_point(self, content: str) -> bool:
        """Check if the file is an entry point."""
        entry_point_indicators = [
            '@SpringBootApplication',
            '@Application',
            'extends Application',
            'implements Application',
            'public static void main(',
            '@WebServlet',
            '@Controller',
            '@RestController'
        ]
        return any(indicator in content for indicator in entry_point_indicators)

    def _is_config_file(self, content: str, file_type: str) -> bool:
        """Check if the file is a configuration file."""
        config_indicators = [
            '@Configuration',
            '@Config',
            'extends Configuration',
            'implements Configuration',
            'application.properties',
            'application.yml',
            'application.yaml'
        ]
        return any(indicator in content for indicator in config_indicators)

    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate complexity score based on various metrics."""
        score = 0.0
        
        # Count methods
        method_count = content.count('public ') + content.count('private ') + content.count('protected ')
        score += min(method_count / 10, 1.0)  # Normalize to 0-1
        
        # Count nested structures
        nested_count = content.count('{') - content.count('}')
        score += min(nested_count / 20, 1.0)  # Normalize to 0-1
        
        # Count lines of code
        loc = len(content.splitlines())
        score += min(loc / 500, 1.0)  # Normalize to 0-1
        
        return score / 3  # Average of all metrics

    def _calculate_dependency_score(self, content: str) -> float:
        """Calculate dependency score based on imports and annotations."""
        score = 0.0
        
        # Count imports
        import_count = content.count('import ')
        score += min(import_count / 20, 1.0)  # Normalize to 0-1
        
        # Count annotations
        annotation_count = content.count('@')
        score += min(annotation_count / 10, 1.0)  # Normalize to 0-1
        
        return score / 2  # Average of all metrics

    def _calculate_business_logic_score(self, content: str) -> float:
        """Calculate business logic score based on business-related patterns."""
        business_indicators = [
            'Service',
            'Repository',
            'DAO',
            'Manager',
            'Handler',
            'Processor',
            'Factory',
            'Builder',
            'Strategy',
            'Command',
            'Observer',
            'State',
            'Template'
        ]
        
        score = 0.0
        for indicator in business_indicators:
            if indicator in content:
                score += 1.0
        
        return min(score / len(business_indicators), 1.0)  # Normalize to 0-1

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