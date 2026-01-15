"""
Logging System for NFL Playoff Predictor
Centralized logging with file and console output
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import LoggingConfig

class NFLLogger:
    """
    Centralized logging system with rotation and formatting
    
    Features:
    - Console and file logging
    - Log rotation (max size, backup count)
    - Different log levels per handler
    - Structured log messages
    
    Usage:
        >>> from logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Fetching 2025 NFL data")
        >>> logger.warning("Sharp money detected on BUF")
        >>> logger.error("API rate limit exceeded")
    """
    
    _loggers = {}  # Cache loggers to avoid duplicates
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name
        
        Args:
            name: Logger name (usually __name__ of calling module)
            
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LoggingConfig.LOG_LEVEL))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler
        if LoggingConfig.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler with rotation
        if LoggingConfig.LOG_TO_FILE:
            log_path = Path(LoggingConfig.LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                LoggingConfig.LOG_FILE,
                maxBytes=LoggingConfig.MAX_LOG_SIZE_MB * 1024 * 1024,
                backupCount=LoggingConfig.BACKUP_COUNT
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger

# Convenience function
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger
    
    Args:
        name: Logger name (use __name__)
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting prediction")
    """
    return NFLLogger.get_logger(name)

# Test the logger
if __name__ == "__main__":
    logger = get_logger("test")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    print("✅ Logger working! Check nfl_predictor.log")
