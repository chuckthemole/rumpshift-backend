"""
shared/api/api_manager.py

Reusable API client abstraction for Django projects.

This module provides a centralized, configurable HTTP client interface
that wraps Python's `requests` library. It is designed for multi-project
repositories where different Django apps share common external API logic.

Features:
- Named API configurations (via API_CONFIG)
- Runtime base URL overrides (for dev/staging/prod environments)
- Optional default endpoint setting
- Built-in request logging and error handling
- Clean, consistent interface for GET/POST calls
"""

import logging
import requests
from requests.exceptions import RequestException, Timeout
from shared.api.config import API_CONFIG


# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Core Client
# -----------------------------------------------------------------------------
class ApiClient:
    """
    A reusable API client for interacting with RESTful services.

    Example:
        >>> api = get_api("CounterAPI", base_url="http://localhost:8000/api")
        >>> api.set_endpoint("/session/data")
        >>> data = api.get()  # GET http://localhost:8000/api/session/data
    """

    DEFAULT_TIMEOUT = 10  # seconds

    def __init__(self, name: str, base_url: str, headers: dict | None = None):
        """
        Initialize a new ApiClient instance.

        Args:
            name (str): Logical name for this API (used in logging).
            base_url (str): Base URL for this API (e.g., 'https://api.example.com').
            headers (dict | None): Optional default headers to send with every request.
        """
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self._default_endpoint = None

    # -------------------------------------------------------------------------
    # Configuration Helpers
    # -------------------------------------------------------------------------
    def set_endpoint(self, endpoint: str):
        """
        Set a default endpoint to use for subsequent GET/POST calls.

        Args:
            endpoint (str): Relative path (e.g., '/users', 'session/data').

        Returns:
            ApiClient: Enables method chaining.
        """
        self._default_endpoint = endpoint.lstrip("/")
        return self

    def _make_url(self, endpoint: str | None = None) -> str:
        """
        Construct the full request URL.

        Args:
            endpoint (str | None): Optional endpoint override.

        Returns:
            str: The full URL for the request.
        """
        if endpoint:
            return f"{self.base_url}/{endpoint.lstrip('/')}"
        if self._default_endpoint:
            return f"{self.base_url}/{self._default_endpoint}"
        raise ValueError("No endpoint specified or set via set_endpoint().")

    # -------------------------------------------------------------------------
    # HTTP Methods
    # -------------------------------------------------------------------------
    def get(
        self,
        endpoint: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        params: dict | None = None,
        json: dict | None = None,
        **kwargs,
    ):
        """
        Perform an HTTP GET request.

        Args:
            endpoint (str | None): Optional endpoint override.
            timeout (int): Timeout in seconds.
            params (dict | None): Query parameters to append to the URL (?key=value).
            json (dict | None): Optional JSON payload to send in the body (if supported by API).
            **kwargs: Additional arguments passed to requests.get().

        Returns:
            dict | list: Parsed JSON response.

        Notes:
            Some APIs accept JSON payloads with GET requests. Not all servers support this.
        """
        url = self._make_url(endpoint)
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=timeout,
                params=params,
                json=json,
                **kwargs
            )
            self._log_request("GET", url, response)
            response.raise_for_status()
            return response.json()
        except Timeout:
            logger.error(f"[{self.name}] GET {url} timed out after {timeout}s")
            raise
        except RequestException as e:
            logger.error(f"[{self.name}] GET {url} failed: {e}")
            raise

    def post(
        self,
        endpoint: str | None = None,
        data=None,
        json=None,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ):
        """
        Perform an HTTP POST request.

        Args:
            endpoint (str | None): Optional endpoint override.
            data (dict | None): Form data to send.
            json (dict | None): JSON payload to send.
            timeout (int): Timeout in seconds.
            **kwargs: Additional arguments passed to requests.post().

        Returns:
            dict | list: Parsed JSON response.
        """
        url = self._make_url(endpoint)
        try:
            response = requests.post(
                url, headers=self.headers, data=data, json=json, timeout=timeout, **kwargs
            )
            self._log_request("POST", url, response)
            response.raise_for_status()
            return response.json()
        except Timeout:
            logger.error(
                f"[{self.name}] POST {url} timed out after {timeout}s")
            raise
        except RequestException as e:
            logger.error(f"[{self.name}] POST {url} failed: {e}")
            raise

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    def _log_request(self, method: str, url: str, response):
        """
        Log request details for observability.

        Args:
            method (str): HTTP method name (GET, POST, etc.).
            url (str): Full request URL.
            response (requests.Response): Response object.
        """
        logger.info(
            "[%s] %s %s -> %d", self.name, method, url, response.status_code
        )


# -----------------------------------------------------------------------------
# Factory Function
# -----------------------------------------------------------------------------
def get_api(api_name: str, base_url: str | None = None) -> ApiClient:
    """
    Factory method to construct an ApiClient from API_CONFIG.

    The consuming app may optionally override the base URL to point to
    environment-specific endpoints (e.g., dev, staging, production).

    Args:
        api_name (str): The logical name of the API (must exist in API_CONFIG).
        base_url (str | None): Optional override for the configured base URL.

    Returns:
        ApiClient: Configured instance ready to make HTTP calls.

    Raises:
        ValueError: If api_name is not defined in API_CONFIG or no base URL is available.
    """
    config = API_CONFIG.get(api_name)
    if not config:
        raise ValueError(f"API '{api_name}' not found in API_CONFIG.")

    resolved_url = base_url or config.get("base_url")
    if not resolved_url:
        raise ValueError(f"No base URL provided for API '{api_name}'.")

    return ApiClient(
        name=api_name,
        base_url=resolved_url,
        headers=config.get("headers", {}),
    )


# -----------------------------------------------------------------------------
# Example Usage (for developers)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: Using a dev API
    api = get_api("CounterAPI", base_url="http://localhost:8000/api")
    api.set_endpoint("/session/data")

    try:
        result = api.get()
        print("Received data:", result)
    except Exception as e:
        logger.exception("Failed to fetch data from CounterAPI.")
