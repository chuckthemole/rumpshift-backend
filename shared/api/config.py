"""
shared/api/config.py

Centralized configuration for API endpoints and defaults.

This module defines base URLs and headers for external APIs used across
Django projects in the repository. It automatically selects the correct
environment (development, staging, or production) based on environment
variables or Django settings.

Usage:
    from shared.api import get_api

    api = get_api("ExampleAPI")  # picks correct base URL automatically
    data = api.get("/session/data")
"""

import os
from typing import Literal

# -----------------------------------------------------------------------------
# Environment Detection
# -----------------------------------------------------------------------------
# Supported environments
ENVIRONMENTS: tuple[Literal["development", "staging", "production"], ...] = (
    "development",
    "staging",
    "production",
)

# Default to development unless explicitly set
APP_ENV = os.getenv("DEVELOPMENT_ENV", "development").lower()

if APP_ENV not in ENVIRONMENTS:
    raise ValueError(
        f"Invalid APP_ENV: {APP_ENV}. Must be one of {ENVIRONMENTS}")

# -----------------------------------------------------------------------------
# Base URLs per Environment
# -----------------------------------------------------------------------------
BASE_URLS = {
    "MainAPI": {
        "development": "http://localhost:8000/api",
        "staging": "https://staging.mainapi.yourcompany.com/api",
        "production": "https://mainapi.yourcompany.com/api",
    },
    "ExampleAPI": {
        "development": "http://localhost:9000/api",
        "staging": "https://staging.counterdata.yourcompany.com/api",
        "production": "https://counterdata.yourcompany.com/api",
    },
}

# -----------------------------------------------------------------------------
# Common Headers
# -----------------------------------------------------------------------------
COMMON_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "MyApp/1.0 (+https://yourcompany.com)",
}

# -----------------------------------------------------------------------------
# API Configuration
# -----------------------------------------------------------------------------
API_CONFIG = {
    "MainAPI": {
        "base_url": BASE_URLS["MainAPI"][APP_ENV],
        "headers": COMMON_HEADERS,
    },
    "ExampleAPI": {
        "base_url": BASE_URLS["ExampleAPI"][APP_ENV],
        "headers": {
            **COMMON_HEADERS,
            # If you have secrets, use environment variables:
            # export COUNTER_API_KEY="my-secret-key"
            "Authorization": f"Bearer {os.getenv('COUNTER_API_KEY', '')}",
        },
    },
}

# -----------------------------------------------------------------------------
# Developer Info
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Loaded API config for environment: {APP_ENV}")
    for api_name, config in API_CONFIG.items():
        print(f"- {api_name}: {config['base_url']}")
