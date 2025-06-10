from setuptools import setup, find_packages

setup(
    name="java-architecture-analyzer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.7",
        "openai>=1.12.0",
        "rich>=13.7.0",
        "pydantic>=2.6.1",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
        "loguru>=0.7.2",
        "ratelimit>=2.2.1",
        "tenacity>=8.2.3",
    ],
    entry_points={
        "console_scripts": [
            "java-analyzer=src.cli:cli",
        ],
    },
) 