import json
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from openai import OpenAI, AzureOpenAI
from loguru import logger
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.models import JavaFile, LLMResponse, ProjectAnalysis
from src.utils.file_utils import sanitize_path, get_project_root


class LLMAnalyzer:
    """Analyzes Java files using LLM to extract architectural insights."""

    def __init__(self):
        self._setup_logging()
        self._setup_llm_client()
        self._setup_rate_limiting()
        self.project_root = None

    def _setup_logging(self) -> None:
        """Configure logging for the LLM analyzer."""
        logger.add(
            settings.LOG_FILE,
            level=settings.LOG_LEVEL,
            rotation="1 day",
            retention="7 days",
        )

    def _setup_llm_client(self) -> None:
        """Configure LLM client based on provider."""
        if settings.LLM_PROVIDER == "azure":
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version="2024-02-15-preview",
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
        else:
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY
            )

    def _setup_rate_limiting(self) -> None:
        """Configure rate limiting decorators."""
        self._call_llm = sleep_and_retry(
            limits(
                calls=settings.RATE_LIMIT_CALLS,
                period=settings.RATE_LIMIT_PERIOD
            )(self._call_llm)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API with rate limiting and retries."""
        print("[LLM] Sending request to LLM API...")
        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=0.3
            )
            print("[LLM] Received response from LLM API.")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise

    def analyze_files(self, files: List[JavaFile]) -> ProjectAnalysis:
        """Analyze a list of Java files and return a ProjectAnalysis object."""
        if not files:
            return ProjectAnalysis(
                project_path="",
                analysis_timestamp=datetime.now(),
                execution_time=0.0,
                architecture_summary="",
                design_patterns={},
                code_quality_metrics={},
                recommendations=[],
                file_analyses=[]
            )

        start_time = time.time()
        analysis_results = []

        # Determine project root from the first file
        if files:
            self.project_root = get_project_root(files[0].path)

        # Group files by package and type
        file_groups = self._group_files(files)
        
        # Process each group
        for group_key, group_files in file_groups.items():
            if len(group_files) == 1:
                # Single file analysis
                result = self._analyze_single_file(group_files[0])
                if result:
                    analysis_results.append(result)
            else:
                # Group analysis
                results = self._analyze_file_group(group_files)
                if results:
                    analysis_results.extend(results)

        # Generate project-wide summary and recommendations
        project_summary = self._generate_project_summary(analysis_results)
        project_recommendations = self._generate_project_recommendations(analysis_results)

        execution_time = time.time() - start_time

        return ProjectAnalysis(
            project_path=str(self.project_root),  # Convert Path to string
            analysis_timestamp=datetime.now(),
            execution_time=execution_time,
            architecture_summary=project_summary,
            design_patterns=self._extract_design_patterns(analysis_results),
            code_quality_metrics=self._extract_quality_metrics(analysis_results),
            recommendations=project_recommendations,
            file_analyses=analysis_results
        )

    def _group_files(self, files: List[JavaFile]) -> Dict[str, List[JavaFile]]:
        """Group files by type and package for batch analysis."""
        groups: Dict[str, List[JavaFile]] = {}
        
        for file in files:
            # Create group key based on file type and package
            group_key = f"{file.file_type}:{file.package}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(file)
        
        return groups

    def _analyze_file_group(self, files: List[JavaFile]) -> List[LLMResponse]:
        """Analyze a group of related files together."""
        if not files:
            return []

        # Create a prompt that includes all files in the group
        file_contents = []
        for file in files:
            # Use relative path in the prompt
            rel_path = sanitize_path(file.path, self.project_root)
            file_contents.append(
                f"File: {rel_path}\n"
                f"Package: {file.package}\n"
                f"Type: {file.file_type}\n"
                f"Content: {file.content}"
            )

        prompt = f"""Analyze these related Java files and provide insights in JSON format for each:

{chr(10).join(file_contents)}

For each file, provide a JSON array of objects with this exact format (no markdown formatting, just the raw JSON):
[
    {{
        "file_path": "relative/path/to/file",
        "architectural_insights": ["list of key architectural insights"],
        "design_patterns": ["list of identified design patterns"],
        "quality_issues": ["list of quality issues"],
        "recommendations": ["list of improvement recommendations"],
        "confidence_score": 0.0 to 1.0,
        "token_usage": {{"total": number}}
    }}
]"""

        try:
            response = self._call_llm(prompt)
            if not response or not response.strip():
                logger.warning(f"Empty response from LLM for group of {len(files)} files")
                return []

            # Clean the response of any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                # Remove markdown code block formatting
                cleaned_response = cleaned_response.split('```', 2)[1]
                if cleaned_response.startswith('json'):
                    cleaned_response = cleaned_response[4:]
                cleaned_response = cleaned_response.strip()

            # Parse the JSON response
            try:
                # Handle both single and multiple file responses
                if cleaned_response.strip().startswith('['):
                    # Multiple file response
                    results = json.loads(cleaned_response)
                else:
                    # Single file response
                    results = [json.loads(cleaned_response)]

                # Convert each result to LLMResponse and map to correct file
                responses = []
                for result in results:
                    # Find the corresponding file using relative paths
                    file_path = result.get('file_path', '')
                    matching_file = next(
                        (f for f in files if sanitize_path(f.path, self.project_root) == file_path),
                        None
                    )
                    
                    if matching_file:
                        response = LLMResponse(
                            file_path=str(matching_file.path),  # Convert Path to string
                            architectural_insights=result.get('architectural_insights', []),
                            design_patterns=result.get('design_patterns', []),
                            quality_issues=result.get('quality_issues', []),
                            recommendations=result.get('recommendations', []),
                            confidence_score=result.get('confidence_score', 0.0),
                            token_usage=result.get('token_usage', {'total': 0})
                        )
                        responses.append(response)
                    else:
                        logger.warning(f"Could not match file path in response: {file_path}")

                return responses

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Raw response: {response}")
                return []

        except Exception as e:
            logger.error(f"Error analyzing file group: {e}")
            return []

    def _extract_json_from_response(self, response: str) -> str:
        """Remove Markdown code block formatting if present."""
        response = response.strip()
        if response.startswith('```'):
            lines = response.splitlines()
            # Remove the first line (``` or ```json)
            if lines[0].startswith('```'):
                lines = lines[1:]
            # Remove the last line if it's closing backticks
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            response = '\n'.join(lines)
        return response

    def _analyze_single_file(self, file: JavaFile) -> Optional[LLMResponse]:
        """Analyze a single Java file using LLM."""
        prompt = self._create_analysis_prompt(file)
        response = self._call_llm(prompt)
        
        try:
            cleaned_response = self._extract_json_from_response(response)
            parsed_response = json.loads(cleaned_response)
            # Create LLMResponse with the file path
            return LLMResponse(
                file_path=file.path,
                architectural_insights=parsed_response.get("architectural_insights", []),
                design_patterns=parsed_response.get("design_patterns", []),
                quality_issues=parsed_response.get("quality_issues", []),
                recommendations=parsed_response.get("recommendations", []),
                confidence_score=parsed_response.get("confidence_score", 0.0),
                token_usage=parsed_response.get("token_usage", {"total": 0})
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for {file.path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating LLMResponse for {file.path}: {str(e)}")
            return None

    def _create_analysis_prompt(self, file: JavaFile) -> str:
        """Create a prompt for analyzing a Java file."""
        return f"""Analyze this Java file and provide insights in JSON format:
        {{
            "architectural_insights": ["list of key architectural insights"],
            "design_patterns": ["list of identified design patterns"],
            "quality_issues": ["list of quality issues"],
            "recommendations": ["list of improvement recommendations"],
            "confidence_score": 0.0 to 1.0,
            "token_usage": {{"total": number}}
        }}

        File: {sanitize_path(file.path, self.project_root)}
        Package: {file.package}
        Type: {file.file_type}
        Content:
        {file.content}
        """

    def _summarize_file_results(self, results: List[LLMResponse], max_files: int = 10) -> str:
        """Create a concise summary of per-file findings for the project-wide LLM call."""
        summaries = []
        for result in results[:max_files]:
            sanitized_path = sanitize_path(result.file_path, self.project_root)
            summary = (
                f"File: {sanitized_path}\n"
                f"  - Architectural Insights: {', '.join(result.architectural_insights) if result.architectural_insights else 'None'}\n"
                f"  - Design Patterns: {', '.join(result.design_patterns) if result.design_patterns else 'None'}\n"
                f"  - Quality Issues: {', '.join(result.quality_issues) if result.quality_issues else 'None'}\n"
                f"  - Recommendations: {', '.join(result.recommendations) if result.recommendations else 'None'}\n"
            )
            summaries.append(summary)
        if len(results) > max_files:
            summaries.append(f"...and {len(results) - max_files} more files analyzed.")
        return '\n'.join(summaries)

    def _generate_architecture_summary(self, results: List[LLMResponse]) -> str:
        """Generate a summary of the project architecture."""
        if not results:
            return "No files were successfully analyzed."
        
        file_summaries = self._summarize_file_results(results)
        prompt = f"""
You are an expert Java architect and code reviewer. The goal of this analysis is to provide a new developer with a clear, concise, and accurate overview of the project's workings and any issues it might have.
By the end of the analysis, the new developer should be able to work on the project and make improvements without having to ask any questions.

Here are the findings from analyzing the following files:
{file_summaries}

Based on these findings, provide a thorough but to-the-point summary of the overall project architecture. Focus on:
1. Overall architecture style
2. Key components and their relationships
3. Main design patterns used
4. Notable architectural decisions
Do not include information or suggestions that are not supported by the findings above. Be specific and base your summary only on the actual findings above.
"""
        try:
            print("[LLM] Generating project-wide summary...")
            return self._call_llm(prompt)
        except Exception as e:
            logger.error(f"Error generating architecture summary: {str(e)}")
            return "Failed to generate architecture summary."

    def _generate_recommendations(self, results: List[LLMResponse]) -> List[str]:
        """Generate project-wide recommendations."""
        if not results:
            return ["No files were successfully analyzed."]
        
        file_summaries = self._summarize_file_results(results)
        prompt = f"""
You are an expert Java architect and code reviewer. The goal of this analysis is to provide a new developer with a clear, concise, and accurate overview of the project's workings and any issues it might have.
By the end of the analysis, the new developer should be able to work on the project and make improvements without having to ask any questions.

Here are the findings from analyzing the following files:
{file_summaries}

Based on these findings, provide a list of high-level, project-wide recommendations for improving the project. Focus on:
1. Architectural improvements
2. Design pattern applications
3. Code quality enhancements
4. Performance optimizations
Do not suggest improvements that are not supported by the findings above. Be specific and base your recommendations only on the actual findings above.
"""
        try:
            print("[LLM] Generating project-wide recommendations...")
            response = self._call_llm(prompt)
            return [line.strip() for line in response.split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Failed to generate recommendations."]

    def _generate_project_summary(self, results: List[LLMResponse]) -> str:
        """Generate a summary of the project architecture."""
        return self._generate_architecture_summary(results)

    def _generate_project_recommendations(self, results: List[LLMResponse]) -> List[str]:
        """Generate project-wide recommendations."""
        return self._generate_recommendations(results)

    def _extract_design_patterns(self, results: List[LLMResponse]) -> Dict[str, List[str]]:
        """Extract design patterns from the analysis results."""
        design_patterns: Dict[str, List[str]] = {}
        for result in results:
            for pattern in result.design_patterns:
                if pattern not in design_patterns:
                    design_patterns[pattern] = []
                design_patterns[pattern].append(sanitize_path(result.file_path, self.project_root))
        return design_patterns

    def _extract_quality_metrics(self, results: List[LLMResponse]) -> Dict[str, float]:
        """Extract quality metrics from the analysis results."""
        quality_metrics: Dict[str, float] = {}
        for result in results:
            quality_metrics[sanitize_path(result.file_path, self.project_root)] = len(result.quality_issues)
        return quality_metrics 