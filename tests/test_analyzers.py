import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.analyzers.file_analyzer import FileAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.core.models import FileType, JavaFile, FileImportance


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
    analyzer = FileAnalyzer()
    files = analyzer.analyze_project(temp_project_dir)
    assert len(files) == 1
    assert isinstance(files[0], JavaFile)
    assert isinstance(files[0].importance, FileImportance)


def test_file_analyzer_importance_calculation(sample_java_file):
    """Test file importance calculation."""
    analyzer = FileAnalyzer()
    importance = analyzer._calculate_file_importance(
        Path("test.java"),
        sample_java_file,
        "class"
    )
    assert isinstance(importance, FileImportance)
    assert importance.business_logic_score > 0  # Should detect @Service
    assert importance.total_score > 0


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
        path=Path("test.java"),
        package="com.example",
        content="test",
        file_type="class",
        importance=FileImportance()
    )
    
    result = analyzer._analyze_single_file(java_file)
    assert result.architectural_insights == ["Service layer implementation"]
    assert result.design_patterns == ["Service Pattern"]
    assert result.quality_issues == []
    assert result.recommendations == ["Add documentation"]
    assert result.confidence_score == 0.9


@patch("openai.ChatCompletion.create")
def test_llm_analyzer_batch_analysis(mock_openai):
    """Test batch analysis of multiple files."""
    # Mock LLM response for batch analysis
    mock_response = {
        "choices": [{
            "message": {
                "content": """
                [
                    {
                        "file_path": "test1.java",
                        "architectural_insights": ["Service implementation"],
                        "design_patterns": ["Service Pattern"],
                        "quality_issues": [],
                        "recommendations": ["Add docs"],
                        "confidence_score": 0.9,
                        "token_usage": {"total": 100}
                    },
                    {
                        "file_path": "test2.java",
                        "architectural_insights": ["Repository implementation"],
                        "design_patterns": ["Repository Pattern"],
                        "quality_issues": [],
                        "recommendations": ["Add docs"],
                        "confidence_score": 0.9,
                        "token_usage": {"total": 100}
                    }
                ]
                """
            }
        }]
    }
    mock_openai.return_value = mock_response
    
    analyzer = LLMAnalyzer()
    files = [
        JavaFile(
            path=Path("test1.java"),
            package="com.example",
            content="test1",
            file_type="class",
            importance=FileImportance()
        ),
        JavaFile(
            path=Path("test2.java"),
            package="com.example",
            content="test2",
            file_type="class",
            importance=FileImportance()
        )
    ]
    
    results = analyzer._analyze_file_batch(files)
    assert len(results) == 2
    assert results[0].file_path == Path("test1.java")
    assert results[1].file_path == Path("test2.java") 