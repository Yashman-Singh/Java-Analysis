import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

from src.core.models import ProjectAnalysis
from src.utils.file_utils import sanitize_path

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates analysis reports in various formats."""

    def generate_report(self, analysis: ProjectAnalysis, output_path: str) -> None:
        """Generate a markdown report from the analysis results."""
        try:
            logger.info(f"Starting report generation for {len(analysis.file_analyses)} files")
            report = []
            
            # Project Overview
            report.append("# Java Project Analysis Report\n")
            report.append(f"## Project Overview\n")
            # Normalize project path for display
            project_path = str(analysis.project_path).replace('\\', '/')
            report.append(f"- **Project Path:** {project_path}\n")
            report.append(f"- **Analysis Timestamp:** {datetime.now().isoformat()}\n")
            report.append(f"- **Execution Time:** {analysis.execution_time:.2f} seconds\n")
            report.append(f"- **Files Analyzed:** {len(analysis.file_analyses)}\n\n")

            # Architecture Summary
            report.append("## Architecture Summary\n")
            report.append(f"{analysis.architecture_summary}\n\n")

            # Design Patterns
            report.append("## Design Patterns\n")
            if analysis.design_patterns:
                for pattern, files in analysis.design_patterns.items():
                    report.append(f"### {pattern}\n")
                    report.append("Found in:\n")
                    for file in files:
                        report.append(f"- {file}\n")
                    report.append("\n")
            else:
                report.append("No design patterns identified.\n\n")

            # Code Quality Metrics
            report.append("## Code Quality Metrics\n")
            if analysis.code_quality_metrics:
                # Calculate column widths
                file_width = max(len("File"), max(len(file) for file in analysis.code_quality_metrics.keys()))
                issues_width = max(len("Issues"), max(len(str(issues)) for issues in analysis.code_quality_metrics.values()))
                
                # Create header and separator
                report.append(f"| {'File':<{file_width}} | {'Issues':<{issues_width}} |")
                report.append(f"|{'-' * file_width}|{'-' * issues_width}|")
                
                # Add rows
                for file, issues in analysis.code_quality_metrics.items():
                    report.append(f"| {file:<{file_width}} | {str(issues):<{issues_width}} |")
                
                # Add newline after table
                report.append("")
            else:
                report.append("No quality metrics available.\n\n")

            # Recommendations
            report.append("## Recommendations\n")
            if analysis.recommendations:
                for rec in analysis.recommendations:
                    report.append(f"- {rec}\n")
                report.append("\n")
            else:
                report.append("No recommendations available.\n\n")

            # File Analysis
            report.append("## File Analysis\n")
            for file_analysis in analysis.file_analyses:
                report.append(f"### {sanitize_path(file_analysis.file_path, analysis.project_path)}\n")
                
                if file_analysis.architectural_insights:
                    report.append("#### Architectural Insights\n")
                    for insight in file_analysis.architectural_insights:
                        report.append(f"- {insight}\n")
                    report.append("\n")
                
                if file_analysis.design_patterns:
                    report.append("#### Design Patterns\n")
                    for pattern in file_analysis.design_patterns:
                        report.append(f"- {pattern}\n")
                    report.append("\n")
                
                if file_analysis.quality_issues:
                    report.append("#### Quality Issues\n")
                    for issue in file_analysis.quality_issues:
                        report.append(f"- {issue}\n")
                    report.append("\n")
                
                if file_analysis.recommendations:
                    report.append("#### Recommendations\n")
                    for rec in file_analysis.recommendations:
                        report.append(f"- {rec}\n")
                    report.append("\n")

            # Write the report
            report_content = '\n'.join(report)
            logger.info(f"Writing report to: {output_path}")
            
            # Ensure we're writing to the correct location
            output_path = os.path.abspath(output_path)
            logger.debug(f"Absolute output path: {output_path}")
            
            # Force write the file with a temporary file to avoid caching issues
            temp_path = f"{output_path}.tmp"
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Move the temporary file to the final location
                os.replace(temp_path, output_path)
                
                # Verify the file was written
                if os.path.exists(output_path):
                    logger.info(f"Report successfully written to: {output_path}")
                    # Print first few lines of the file to verify content
                    with open(output_path, 'r', encoding='utf-8') as f:
                        logger.debug(f"First few lines of report:\n{f.read()[:200]}")
                else:
                    raise IOError(f"Failed to write report to: {output_path}")
            finally:
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            # Create a minimal report with error information
            error_report = [
                "# Java Project Analysis Report\n",
                "## Error\n",
                f"An error occurred while generating the report: {str(e)}\n",
                "\n## Partial Results\n",
                f"- Project Path: {analysis.project_path}\n",
                f"- Files Analyzed: {len(analysis.file_analyses)}\n",
                "\nPlease check the logs for more details."
            ]
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(error_report))
                    f.flush()
                    os.fsync(f.fileno())
                logger.info(f"Error report written to: {output_path}")
            except Exception as write_error:
                logger.error(f"Failed to write error report: {write_error}")
            raise 