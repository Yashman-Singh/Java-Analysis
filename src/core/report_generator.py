from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.core.models import ProjectAnalysis


class ReportGenerator:
    """Generates analysis reports in various formats."""

    def generate_report(self, analysis: ProjectAnalysis) -> str:
        """Generate a markdown report from the analysis results."""
        report = [
            "# Java Project Architecture Analysis Report",
            f"\n## Project Path: {analysis.project_path}",
            f"\n## Analysis Timestamp: {datetime.now().isoformat()}",
            f"\n## Execution Time: {analysis.execution_time_seconds:.2f} seconds",
            
            "\n## Architecture Summary",
            f"\n{analysis.architecture_summary}",
            
            "\n## Design Patterns",
        ]
        
        # Add design patterns
        if analysis.design_patterns:
            for pattern, files in analysis.design_patterns.items():
                report.append(f"\n### {pattern}")
                for file in files:
                    report.append(f"- {file}")
        else:
            report.append("\nNo design patterns identified.")
        
        # Add quality metrics
        report.append("\n## Code Quality Metrics")
        if analysis.quality_metrics:
            for file, issues in analysis.quality_metrics.items():
                report.append(f"\n### {file}")
                report.append(f"- Issues found: {issues}")
        else:
            report.append("\nNo quality metrics available.")
        
        # Add recommendations
        report.append("\n## Recommendations")
        if analysis.recommendations:
            for rec in analysis.recommendations:
                report.append(f"- {rec}")
        else:
            report.append("\nNo recommendations available.")
        
        # Add detailed file analysis
        report.append("\n## Detailed File Analysis")
        for file_analysis in analysis.analyzed_files:
            report.append(f"\n### {file_analysis.file_path}")
            
            if file_analysis.architectural_insights:
                report.append("\n#### Architectural Insights")
                for insight in file_analysis.architectural_insights:
                    report.append(f"- {insight}")
            
            if file_analysis.design_patterns:
                report.append("\n#### Design Patterns")
                for pattern in file_analysis.design_patterns:
                    report.append(f"- {pattern}")
            
            if file_analysis.quality_issues:
                report.append("\n#### Quality Issues")
                for issue in file_analysis.quality_issues:
                    report.append(f"- {issue}")
            
            if file_analysis.recommendations:
                report.append("\n#### Recommendations")
                for rec in file_analysis.recommendations:
                    report.append(f"- {rec}")
        
        return "\n".join(report) 