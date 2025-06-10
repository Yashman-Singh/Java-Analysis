import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.analyzers.file_analyzer import FileAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.core.models import FileType, JavaFile


@pytest.fixture
def sample_java_file():
    """Create a sample Java file for testing."""
    content = """
    package com.example;
    
    import org.springframework.stereotype.Service;
    import java.util.List;
    
    @Service
    public class SampleService {
        public List<String> getData() {
            return List.of("test");
        }
    }
    """
    return content


@pytest.fixture
def temp_project_dir(tmp_path, sample_java_file):
    """Create a temporary project directory with sample files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create sample Java files
    (project_dir / "src" / "main" / "java" / "com" / "example").mkdir(parents=True)
    service_file = project_dir / "src" / "main" / "java" / "com" / "example" / "SampleService.java"
    service_file.write_text(sample_java_file)
    
    return project_dir


def test_file_analyzer_initialization(temp_project_dir):
    """Test FileAnalyzer initialization."""
    analyzer = FileAnalyzer(str(temp_project_dir))
    assert analyzer.project_path == temp_project_dir
    assert isinstance(analyzer.java_files, dict)
    assert isinstance(analyzer.file_importance_scores, dict)


def test_file_analyzer_find_java_files(temp_project_dir):
    """Test finding Java files in a project."""
    analyzer = FileAnalyzer(str(temp_project_dir))
    java_files = analyzer._find_java_files()
    assert len(java_files) == 1
    assert java_files[0].name == "SampleService.java"


def test_file_analyzer_determine_file_type(sample_java_file):
    """Test determining file type from content."""
    analyzer = FileAnalyzer("dummy_path")
    file_type = analyzer._determine_file_type(sample_java_file, "SampleService.java")
    assert file_type == FileType.SERVICE


@patch("openai.ChatCompletion.create")
def test_llm_analyzer_initialization(mock_openai):
    """Test LLMAnalyzer initialization."""
    analyzer = LLMAnalyzer()
    assert analyzer is not None


@patch("openai.ChatCompletion.create")
def test_llm_analyzer_analyze_single_file(mock_openai):
    """Test analyzing a single file with LLM."""
    # Mock LLM response
    mock_response = {
        "choices": [{
            "message": {
                "content": """
                {
                    "architectural_insights": ["Service layer implementation"],
                    "design_patterns": ["Service Pattern"],
                    "quality_issues": [],
                    "recommendations": ["Add documentation"],
                    "confidence_score": 0.9,
                    "token_usage": {"total": 100}
                }
                """
            }
        }]
    }
    mock_openai.return_value = mock_response
    
    analyzer = LLMAnalyzer()
    java_file = JavaFile(
        path="test.java",
        package="com.example",
        imports=[],
        file_type=FileType.SERVICE,
        importance_score=0.0,
        content="test",
        last_modified=None,
        size_bytes=0
    )
    
    result = analyzer._analyze_single_file(java_file)
    assert result.architectural_insights == ["Service layer implementation"]
    assert result.design_patterns == ["Service Pattern"]
    assert result.quality_issues == []
    assert result.recommendations == ["Add documentation"]
    assert result.confidence_score == 0.9 