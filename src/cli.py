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
                # Sort files by importance score
                files.sort(key=lambda x: x.importance.total_score, reverse=True)
                # Take top N files
                files = files[:max_files]
                console.print(f"[green]Selected top {max_files} most important files for analysis[/green]")
            
            # Perform LLM analysis
            progress.add_task("Performing LLM analysis...", total=None)
            analysis = llm_analyzer.analyze_files(files)
            
            # Generate report
            progress.add_task("Generating report...", total=None)
            report_generator = ReportGenerator()
            try:
                report_generator.generate_report(analysis, output_path)
                console.print(f"\n[green]Analysis complete! Report saved to: {output_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                console.print("A partial report has been generated with available information.")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()


def main():
    """Main entry point for the CLI."""
    try:
        args = parse_args()
        
        # Initialize analyzers
        file_analyzer = FileAnalyzer()
        llm_analyzer = LLMAnalyzer()
        
        # Analyze project
        print(f"Project path: {args.project_path}")
        print(f"Output path: {args.output}")
        print(f"Max files to analyze: {args.max_files}")
        
        # Get list of Java files
        java_files = file_analyzer.analyze_project(
            project_path=args.project_path,
            max_files=args.max_files
        )
        
        if not java_files:
            print("No Java files found to analyze.")
            return
        
        # Perform LLM analysis
        analysis = llm_analyzer.analyze_files(java_files)
        
        # Generate report
        report_generator = ReportGenerator()
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Generate and write the report
            logger.info(f"Generating report at: {args.output}")
            report_generator.generate_report(analysis, args.output)
            
            # Verify the file was written
            if os.path.exists(args.output):
                logger.info(f"Report successfully written to: {args.output}")
                print(f"\nAnalysis complete! Report saved to: {args.output}")
            else:
                logger.error(f"Report file was not created at: {args.output}")
                print(f"\nError: Report file was not created at {args.output}")
                return 1
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            print(f"\nError: {e}")
            print("A partial report has been generated with available information.")
            return 1
            
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        print(f"\nError: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    cli() 