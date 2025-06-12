from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Provider Settings
    LLM_PROVIDER: str = "openai"  # or "azure"
    MODEL_NAME: str = "gpt-4o"  # OpenAI model name or Azure deployment name
    MAX_TOKENS: int = 1000  # Maximum tokens for LLM responses
    
    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    
    # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    
    # Analysis Settings
    MAX_FILE_SIZE: int = 1_000_000  # 1MB
    SUPPORTED_EXTENSIONS: set[str] = {".java"}
    EXCLUDE_PATTERNS: set[str] = {
        "target/",
        "build/",
        "out/",
        ".git/",
        "node_modules/",
        "*.test.java",
        "*.spec.java"
    }
    
    # Cache Settings
    CACHE_DIR: Path = Path.home() / ".java-analyzer" / "cache"
    CACHE_ENABLED: bool = True
    CACHE_EXPIRY_DAYS: int = 7
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = Path.home() / ".java-analyzer" / "logs" / "analyzer.log"
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = 60  # calls per period
    RATE_LIMIT_PERIOD: int = 60  # period in seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_paths()
    
    def _setup_paths(self) -> None:
        """Ensure all paths are absolute and create necessary directories."""
        # Convert relative paths to absolute
        self.CACHE_DIR = self.CACHE_DIR.resolve()
        self.LOG_FILE = self.LOG_FILE.resolve()
        
        # Create necessary directories
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate LLM settings
        if self.LLM_PROVIDER == "azure":
            if not self.AZURE_OPENAI_API_KEY or not self.AZURE_OPENAI_ENDPOINT:
                raise ValueError("Azure OpenAI API key and endpoint are required when using Azure provider")
        elif self.LLM_PROVIDER == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is required when using OpenAI provider")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}")


# Create global settings instance
settings = Settings() 