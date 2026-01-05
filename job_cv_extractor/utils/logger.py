"""
Logging Configuration Module

Provides centralized logging for the application with both file and console handlers.
Logs are written to logs/app.log and can be displayed in Streamlit.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List
import threading


class StreamlitLogHandler(logging.Handler):
    """
    Custom logging handler that stores log messages for Streamlit display.
    Thread-safe implementation for capturing logs during async operations.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.logs = []
                cls._instance.max_logs = 100  # Keep last 100 logs
            return cls._instance
    
    def emit(self, record: logging.LogRecord) -> None:
        """Store formatted log message."""
        try:
            msg = self.format(record)
            with self._lock:
                self.logs.append({
                    'level': record.levelname,
                    'message': msg,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                # Keep only recent logs
                if len(self.logs) > self.max_logs:
                    self.logs = self.logs[-self.max_logs:]
        except Exception:
            self.handleError(record)
    
    def get_logs(self) -> List[dict]:
        """Return copy of stored logs."""
        with self._lock:
            return list(self.logs)
    
    def clear_logs(self) -> None:
        """Clear all stored logs."""
        with self._lock:
            self.logs = []


def setup_logger(name: str = "job_extractor") -> logging.Logger:
    """
    Configure and return the application logger.
    
    Sets up:
    - File handler (logs/app.log) with detailed formatting
    - Console handler for development
    - Streamlit handler for UI display
    
    Args:
        name: Logger name (default: "job_extractor")
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if not exists
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Detailed format for file logging
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for console and Streamlit
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - captures everything
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler - info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Streamlit handler - for UI display
    streamlit_handler = StreamlitLogHandler()
    streamlit_handler.setLevel(logging.INFO)
    streamlit_handler.setFormatter(simple_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(streamlit_handler)
    
    return logger


def get_streamlit_logs() -> List[dict]:
    """Get logs for Streamlit display."""
    handler = StreamlitLogHandler()
    return handler.get_logs()


def clear_streamlit_logs() -> None:
    """Clear Streamlit log buffer."""
    handler = StreamlitLogHandler()
    handler.clear_logs()


# Create default logger instance
logger = setup_logger()

