from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Types of Java files based on their role in the architecture."""
    
    MAIN = "main"
    CONFIG = "config"
    SERVICE = "service"
    CONTROLLER = "controller"
    REPOSITORY = "repository"
    MODEL = "model"
    UTILITY = "utility"
    UNKNOWN = "unknown"


class FileImport(BaseModel):
    """Represents a Java import statement."""
    
    package: str
    class_name: str
    is_static: bool = False


class JavaFile(BaseModel):
    """Represents a Java source file."""
    path: Path
    content: str
    package: str
    file_type: str


class AnalysisResult(BaseModel):
    """Results of analyzing a Java file."""
    
    file: JavaFile
    architectural_role: str
    design_patterns: List[str] = Field(default_factory=list)
    quality_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class LLMResponse(BaseModel):
    """Response from LLM analysis of a Java file."""
    file_path: Path
    architectural_insights: List[str] = Field(default_factory=list)
    design_patterns: List[str] = Field(default_factory=list)
    quality_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    token_usage: Dict[str, int] = Field(default_factory=dict)


class ProjectAnalysis(BaseModel):
    """Complete analysis of a Java project."""
    project_path: str
    analyzed_files: List[LLMResponse]
    architecture_summary: str
    design_patterns: Dict[str, List[str]]
    quality_metrics: Dict[str, float]
    recommendations: List[str]
    execution_time_seconds: float 