import os
from pathlib import Path


class LoggerConfig:
    """
    Shared configuration for all logger instances across projects.
    """

    # Environment
    ENV = os.getenv("DEVELOPMENT_ENV", "development").lower()
    APP_NAME = os.getenv("APP_NAME", "MyApp")

    # Logging settings
    LOG_LEVEL = os.getenv(
        "LOG_LEVEL", "DEBUG" if ENV == "development" else "INFO")
    USE_JSON_LOGS = os.getenv("USE_JSON_LOGS", "false").lower() == "true"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"

    # File logging directory
    LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))
    LOG_FILE = LOG_DIR / f"{APP_NAME.lower()}.log"

    @classmethod
    def is_production(cls):
        return cls.ENV == "production"

    @classmethod
    def is_development(cls):
        return cls.ENV == "development"

    @classmethod
    def is_staging(cls):
        return cls.ENV == "staging"
