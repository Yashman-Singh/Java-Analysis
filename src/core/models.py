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


class FileImportance(BaseModel):
    """Importance metrics for a Java file."""
    is_main_class: bool = False
    is_entry_point: bool = False
    is_config_file: bool = False
    complexity_score: float = 0.0
    dependency_score: float = 0.0
    business_logic_score: float = 0.0
    total_score: float = 0.0

    def calculate_total_score(self) -> float:
        """Calculate the total importance score."""
        weights = {
            'is_main_class': 5.0,
            'is_entry_point': 4.0,
            'is_config_file': 3.0,
            'complexity_score': 2.0,
            'dependency_score': 2.0,
            'business_logic_score': 3.0
        }
        
        self.total_score = (
            (self.is_main_class * weights['is_main_class']) +
            (self.is_entry_point * weights['is_entry_point']) +
            (self.is_config_file * weights['is_config_file']) +
            (self.complexity_score * weights['complexity_score']) +
            (self.dependency_score * weights['dependency_score']) +
            (self.business_logic_score * weights['business_logic_score'])
        )
        return self.total_score


class JavaFile(BaseModel):
    """Represents a Java source file."""
    path: Path
    content: str
    package: str
    file_type: str
    importance: FileImportance = Field(default_factory=FileImportance)


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
    """Model for project-wide analysis results."""
    project_path: str
    analysis_timestamp: datetime
    execution_time: float
    architecture_summary: str
    design_patterns: Dict[str, List[str]]
    code_quality_metrics: Dict[str, float]
    recommendations: List[str]
    file_analyses: List[LLMResponse] 