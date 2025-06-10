import json
import time
from typing import Dict, List, Optional

from openai import OpenAI, AzureOpenAI
from loguru import logger
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.models import JavaFile, LLMResponse, ProjectAnalysis


class LLMAnalyzer:
    """Analyzes Java files using LLM to extract architectural insights."""

    def __init__(self):
        self._setup_logging()
        self._setup_llm_client()
        self._setup_rate_limiting()

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
    def _call_llm(self, prompt: str) -> Dict:
        """Make a call to the LLM API with retry logic."""
        try:
            if settings.LLM_PROVIDER == "azure":
                response = self.client.chat.completions.create(
                    model=settings.MODEL_NAME,  # Azure deployment name
                    messages=[
                        {"role": "system", "content": "You are an expert Java architect and code reviewer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=settings.MAX_TOKENS
                )
            else:
                response = self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an expert Java architect and code reviewer."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=settings.MAX_TOKENS
                )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            raise

    def analyze_files(self, files: List[JavaFile]) -> ProjectAnalysis:
        """Analyze a list of Java files using LLM."""
        logger.info(f"Starting LLM analysis of {len(files)} files using {settings.LLM_PROVIDER}")
        
        analysis_results = []
        design_patterns: Dict[str, List[str]] = {}
        quality_metrics: Dict[str, float] = {}
        start_time = time.time()
        
        for file in files:
            try:
                result = self._analyze_single_file(file)
                if result:
                    analysis_results.append(result)
                    
                    # Aggregate design patterns
                    for pattern in result.design_patterns:
                        if pattern not in design_patterns:
                            design_patterns[pattern] = []
                        design_patterns[pattern].append(str(file.path))
                    
                    # Update quality metrics
                    quality_metrics[str(file.path)] = len(result.quality_issues)
                
            except Exception as e:
                logger.error(f"Error analyzing {file.path}: {str(e)}")
        
        # Generate project-wide analysis
        architecture_summary = self._generate_architecture_summary(analysis_results)
        recommendations = self._generate_recommendations(analysis_results)
        
        return ProjectAnalysis(
            project_path=str(files[0].path.parent),
            analyzed_files=analysis_results,
            architecture_summary=architecture_summary,
            design_patterns=design_patterns,
            quality_metrics=quality_metrics,
            recommendations=recommendations,
            execution_time_seconds=time.time() - start_time
        )

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

        File: {file.path}
        Package: {file.package}
        Type: {file.file_type}
        Content:
        {file.content}
        """

    def _summarize_file_results(self, results: List[LLMResponse], max_files: int = 10) -> str:
        """Create a concise summary of per-file findings for the project-wide LLM call."""
        summaries = []
        for result in results[:max_files]:
            summary = (
                f"File: {result.file_path}\n"
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
            response = self._call_llm(prompt)
            return [line.strip() for line in response.split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Failed to generate recommendations."] 