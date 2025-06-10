import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.analyzers.file_analyzer import FileAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.core.config import settings
from src.core.report_generator import ReportGenerator


console = Console()


@click.group()
def cli():
    """Java Architecture Analyzer - Analyze Java project architecture and design patterns."""
    pass


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="analysis_report.md",
    help="Output file path for the analysis report",
)
@click.option(
    "--max-files",
    "-m",
    type=int,
    default=20,
    help="Maximum number of files to analyze",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def analyze(project_path: str, output: str, max_files: int, verbose: bool):
    """Analyze a Java project and generate an architecture report."""
    try:
        project_path = Path(project_path).resolve()
        output_path = Path(output).resolve()
        
        if verbose:
            console.print(f"Project path: {project_path}")
            console.print(f"Output path: {output_path}")
            console.print(f"Max files to analyze: {max_files}")
        
        # Initialize analyzers
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Initializing analyzers...", total=None)
            
            file_analyzer = FileAnalyzer()
            llm_analyzer = LLMAnalyzer()
            
            # Analyze files
            progress.add_task("Analyzing Java files...", total=None)
            files = file_analyzer.analyze_project(project_path)
            
            if len(files) > max_files:
                console.print(f"[yellow]Warning: Found {len(files)} files, limiting analysis to {max_files} files[/yellow]")
                files = files[:max_files]
            
            # Perform LLM analysis
            progress.add_task("Performing LLM analysis...", total=None)
            analysis = llm_analyzer.analyze_files(files)
            
            # Generate report
            progress.add_task("Generating report...", total=None)
            report_generator = ReportGenerator()
            report = report_generator.generate_report(analysis)
            
            # Save report
            output_path.write_text(report)
            
            console.print(f"\n[green]Analysis complete! Report saved to: {output_path}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    cli() 