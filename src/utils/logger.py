"""Logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logger(
    name: str = "movidesk_automation",
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Setup and configure logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        use_colors: Use colored output in console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler - DISABLED due to Windows cp1252 encoding issues with Unicode
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.DEBUG)
    
    # # Format console output
    # if use_colors and HAS_COLORLOG:
    #     console_formatter = colorlog.ColoredFormatter(
    #         '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #         datefmt='%Y-%m-%d %H:%M:%S',
    #         log_colors={
    #             'DEBUG': 'cyan',
    #             'INFO': 'green',
    #             'WARNING': 'yellow',
    #             'ERROR': 'red',
    #             'CRITICAL': 'red,bg_white',
    #         }
    #     )
    # else:
    #     console_formatter = logging.Formatter(
    #         '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #         datefmt='%Y-%m-%d %H:%M:%S'
    #     )
    # 
    # console_handler.setFormatter(console_formatter)
    # logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "movidesk_automation") -> logging.Logger:
    """Get existing logger or create a basic one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Setup basic logger if not configured
        setup_logger(name)
    return logger
