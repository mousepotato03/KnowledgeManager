"""
Configuration management for RAG indexing pipeline
Handles loading and validation of configuration from YAML files and environment variables
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import yaml
from pydantic import BaseModel, Field, validator
from loguru import logger

@dataclass
class ProcessingSettings:
    """Processing configuration settings"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    processing_version: str = "1.0"
    embedding_model: str = "text-embedding-004"
    batch_size: int = 10
    rate_limit_delay: float = 0.1
    max_retries: int = 3

@dataclass  
class DatabaseSettings:
    """Database configuration settings"""
    chunk_table: str = "rag_knowledge_chunks"
    tools_table: str = "tools"
    similarity_threshold: float = 0.78
    max_matches: int = 10

@dataclass
class LoggingSettings:
    """Logging configuration settings"""
    level: str = "INFO"
    console_format: str = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    file_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    log_file: str = "logs/rag_indexer.log"
    max_file_size: str = "10 MB"
    retention: str = "1 week"
    rotation: str = "10 MB"

@dataclass
class QualitySettings:
    """Quality scoring configuration"""
    base_score: float = 0.5
    optimal_min: int = 200
    optimal_max: int = 1500
    length_bonus: float = 0.2
    structure_indicators: List[str] = field(default_factory=lambda: [
        "however", "therefore", "because", "furthermore", "additionally", "consequently"
    ])
    technical_indicators: List[str] = field(default_factory=lambda: [
        "api", "feature", "integration", "performance", "configuration", "implementation"
    ])
    sentence_min: int = 3
    sentence_max: int = 10
    sentence_bonus: float = 0.1

@dataclass
class SecuritySettings:
    """Security and validation settings"""
    validate_urls: bool = True
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    max_file_size: str = "50MB"
    scan_for_sensitive_data: bool = False

class RAGConfig:
    """Main configuration class for RAG indexing pipeline"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config_data = self._load_config()
        
        # Initialize settings
        self.processing = self._load_processing_settings()
        self.database = self._load_database_settings()
        self.logging = self._load_logging_settings()
        self.quality = self._load_quality_settings()
        self.security = self._load_security_settings()
        
        # Environment-specific settings
        self.supabase_url = self._get_env_var("NEXT_PUBLIC_SUPABASE_URL")
        self.supabase_key = self._get_env_var("SUPABASE_SERVICE_ROLE_KEY")
        self.google_api_key = self._get_env_var("GOOGLE_API_KEY")
        
        # Validate configuration
        self._validate_config()

    def _find_config_file(self) -> str:
        """Find configuration file in standard locations"""
        possible_paths = [
            Path(__file__).parent / "config.yaml",
            Path(__file__).parent / "config.yml",
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        logger.warning("No configuration file found, using defaults")
        return ""

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path or not Path(self.config_path).exists():
            logger.info("Using default configuration")
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            return {}

    def _load_processing_settings(self) -> ProcessingSettings:
        """Load processing settings from config"""
        processing_config = self.config_data.get('processing', {})
        return ProcessingSettings(
            chunk_size=processing_config.get('chunk_size', 1000),
            chunk_overlap=processing_config.get('chunk_overlap', 200),
            min_chunk_size=processing_config.get('min_chunk_size', 100),
            max_chunk_size=processing_config.get('max_chunk_size', 2000),
            processing_version=processing_config.get('processing_version', '1.0'),
            embedding_model=processing_config.get('embedding_model', 'text-embedding-004'),
            batch_size=processing_config.get('batch_size', 10),
            rate_limit_delay=processing_config.get('rate_limit_delay', 0.1),
            max_retries=processing_config.get('max_retries', 3)
        )

    def _load_database_settings(self) -> DatabaseSettings:
        """Load database settings from config"""
        db_config = self.config_data.get('database', {})
        return DatabaseSettings(
            chunk_table=db_config.get('chunk_table', 'rag_knowledge_chunks'),
            tools_table=db_config.get('tools_table', 'tools'),
            similarity_threshold=db_config.get('similarity_threshold', 0.78),
            max_matches=db_config.get('max_matches', 10)
        )

    def _load_logging_settings(self) -> LoggingSettings:
        """Load logging settings from config"""
        log_config = self.config_data.get('logging', {})
        return LoggingSettings(
            level=log_config.get('level', 'INFO'),
            console_format=log_config.get('console_format', 
                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"),
            file_format=log_config.get('file_format',
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
            log_file=log_config.get('log_file', 'logs/rag_indexer.log'),
            max_file_size=log_config.get('max_file_size', '10 MB'),
            retention=log_config.get('retention', '1 week'),
            rotation=log_config.get('rotation', '10 MB')
        )

    def _load_quality_settings(self) -> QualitySettings:
        """Load quality scoring settings from config"""
        quality_config = self.config_data.get('quality', {})
        return QualitySettings(
            base_score=quality_config.get('base_score', 0.5),
            optimal_min=quality_config.get('length_bonus', {}).get('optimal_min', 200),
            optimal_max=quality_config.get('length_bonus', {}).get('optimal_max', 1500),
            length_bonus=quality_config.get('length_bonus', {}).get('bonus', 0.2),
            structure_indicators=quality_config.get('structure_indicators', [
                "however", "therefore", "because", "furthermore", "additionally", "consequently"
            ]),
            technical_indicators=quality_config.get('technical_indicators', [
                "api", "feature", "integration", "performance", "configuration", "implementation"
            ]),
            sentence_min=quality_config.get('sentence_range', {}).get('min', 3),
            sentence_max=quality_config.get('sentence_range', {}).get('max', 10),
            sentence_bonus=quality_config.get('sentence_range', {}).get('bonus', 0.1)
        )

    def _load_security_settings(self) -> SecuritySettings:
        """Load security settings from config"""
        security_config = self.config_data.get('security', {})
        return SecuritySettings(
            validate_urls=security_config.get('validate_urls', True),
            allowed_domains=security_config.get('allowed_domains', []),
            blocked_domains=security_config.get('blocked_domains', []),
            max_file_size=security_config.get('max_file_size', '50MB'),
            scan_for_sensitive_data=security_config.get('scan_for_sensitive_data', False)
        )

    def _get_env_var(self, var_name: str, required: bool = True) -> Optional[str]:
        """Get environment variable with optional requirement check"""
        value = os.getenv(var_name)
        if required and not value:
            logger.warning(f"Required environment variable {var_name} not found")
        return value

    def _validate_config(self) -> None:
        """Validate configuration settings"""
        errors = []
        
        # Validate processing settings
        if self.processing.chunk_size < 100:
            errors.append("chunk_size must be at least 100")
        if self.processing.chunk_overlap >= self.processing.chunk_size:
            errors.append("chunk_overlap must be less than chunk_size")
        if self.processing.batch_size < 1:
            errors.append("batch_size must be at least 1")
        
        # Validate database settings
        if self.database.similarity_threshold < 0 or self.database.similarity_threshold > 1:
            errors.append("similarity_threshold must be between 0 and 1")
        if self.database.max_matches < 1:
            errors.append("max_matches must be at least 1")
        
        # Validate quality settings
        if self.quality.base_score < 0 or self.quality.base_score > 1:
            errors.append("base_score must be between 0 and 1")
        
        # Validate environment variables
        if not self.supabase_url:
            errors.append("NEXT_PUBLIC_SUPABASE_URL environment variable is required")
        if not self.supabase_key:
            errors.append("SUPABASE_SERVICE_ROLE_KEY environment variable is required")  
        if not self.google_api_key:
            errors.append("GOOGLE_API_KEY environment variable is required")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")

    def get_source_type_config(self, source_type: str) -> Dict[str, Any]:
        """Get configuration for a specific source type"""
        source_types = self.config_data.get('source_types', {})
        return source_types.get(source_type, {})

    def is_url_allowed(self, url: str) -> bool:
        """Check if URL is allowed based on security settings"""
        from urllib.parse import urlparse
        
        if not self.security.validate_urls:
            return True
        
        domain = urlparse(url).netloc.lower()
        
        # Check blocked domains
        if domain in [d.lower() for d in self.security.blocked_domains]:
            return False
        
        # Check allowed domains (if specified)
        if self.security.allowed_domains:
            return domain in [d.lower() for d in self.security.allowed_domains]
        
        return True

    def parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('B'):
            size_str = size_str[:-1]
        
        multipliers = {
            'K': 1024,
            'M': 1024 ** 2,
            'G': 1024 ** 3,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-len(suffix)]) * multiplier)
        
        # Assume bytes if no suffix
        return int(size_str)

    def setup_logging(self) -> None:
        """Setup logging based on configuration"""
        from loguru import logger
        
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sys.stdout,
            format=self.logging.console_format,
            level=self.logging.level
        )
        
        # Add file handler
        log_path = Path(self.logging.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            format=self.logging.file_format,
            level="DEBUG",
            rotation=self.logging.rotation,
            retention=self.logging.retention
        )
        
        logger.info(f"Logging configured - Level: {self.logging.level}")

    def to_processing_config(self):
        """Convert to ProcessingConfig for backward compatibility"""
        from rag_indexer import ProcessingConfig
        
        return ProcessingConfig(
            chunk_size=self.processing.chunk_size,
            chunk_overlap=self.processing.chunk_overlap,
            min_chunk_size=self.processing.min_chunk_size,
            max_chunk_size=self.processing.max_chunk_size,
            processing_version=self.processing.processing_version,
            embedding_model=self.processing.embedding_model,
            batch_size=self.processing.batch_size,
            rate_limit_delay=self.processing.rate_limit_delay,
            max_retries=self.processing.max_retries
        )

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"""RAG Configuration:
  Processing: chunk_size={self.processing.chunk_size}, overlap={self.processing.chunk_overlap}
  Database: similarity_threshold={self.database.similarity_threshold}
  Logging: level={self.logging.level}
  Config file: {self.config_path or 'None (using defaults)'}"""