# Java Project Architecture Analysis System

A production-grade Python system for analyzing Java project architecture, providing comprehensive insights into design patterns, components, and code quality.

## Features

- Quick architectural insights without deep code review
- Identification of key components and their relationships
- Analysis of core business logic and data flow
- Detection of potential architectural issues
- Assessment of code quality and maintainability

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd java-analysis
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other configurations
```

## Usage

Basic usage:
```bash
java-analyzer analyze /path/to/java/project
```

Advanced usage:
```bash
java-analyzer analyze /path/to/java/project --max-files 20 --output report.md --verbose
```

For more options:
```bash
java-analyzer --help
```

## Project Structure

```
java-architecture-analyzer/
├── src/
│   ├── analyzers/
│   │   ├── file_analyzer.py    # Java file parsing and analysis
│   │   └── llm_analyzer.py     # LLM integration and analysis
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── models.py          # Data models
│   │   └── report_generator.py # Report generation
│   ├── utils/
│   │   ├── file_utils.py      # File operations
│   │   └── prompt_utils.py    # LLM prompt management
│   └── cli.py                 # Command-line interface
├── tests/
│   └── test_analyzers.py
├── requirements.txt
└── README.md
```
