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
cd java-architecture-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
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
java-analyzer analyze /path/to/java/project --max-files 20 --output report.md
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
│   │   ├── file_analyzer.py
│   │   └── llm_analyzer.py
│   ├── core/
│   │   ├── config.py
│   │   └── models.py
│   ├── utils/
│   │   ├── file_utils.py
│   │   └── prompt_utils.py
│   └── cli.py
├── tests/
│   └── test_analyzers.py
├── requirements.txt
└── README.md
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Run type checking:
```bash
mypy src/
```

4. Format code:
```bash
black src/
isort src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 