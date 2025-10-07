import logging
import sys
import structlog
from pathlib import Path
from .config import LoggerConfig


def _configure_standard_logging():
    """Configures the built-in logging module."""
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    handlers.append(console_handler)

    # Optional file handler
    if LoggerConfig.LOG_TO_FILE:
        LoggerConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LoggerConfig.LOG_FILE)
        file_handler.setFormatter(console_format)
        handlers.append(file_handler)

    logging.basicConfig(
        level=LoggerConfig.LOG_LEVEL,
        handlers=handlers,
    )


def _configure_structlog():
    """Configures structlog for structured JSON logging."""
    shared_processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Renderer depends on environment
    if LoggerConfig.USE_JSON_LOGS or LoggerConfig.is_production():
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(LoggerConfig.LOG_LEVEL)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """
    Returns a structured logger that uses structlog under the hood.
    Example:
        from shared.logger import get_logger
        logger = get_logger(__name__)
        logger.info("User logged in", user_id=123)
    """
    _configure_standard_logging()
    _configure_structlog()
    return structlog.get_logger(name or LoggerConfig.APP_NAME)
