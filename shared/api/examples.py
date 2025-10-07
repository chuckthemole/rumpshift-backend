"""
Example usage of the shared ApiClient and get_api() factory.

This module demonstrates common patterns for consuming APIs using
the shared API client abstraction. It is intended for developers
and can serve as reference documentation.

Key Features:
- Environment-aware API base URL overrides
- Default endpoint usage
- GET and POST requests with error handling
- Logging of requests and responses
"""

import logging
from shared.api.api_client import get_api

# -------------------------------------------------------------------------
# Configure basic logging for examples
# -------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_examples")


# -------------------------------------------------------------------------
# Example 1: Simple GET request using default endpoint
# -------------------------------------------------------------------------
def example_get_default_endpoint():
    """
    Fetch session data from ExampleAPI using a default endpoint.

    Shows how to set a default endpoint for repeated GET requests.
    """
    api = get_api("ExampleAPI", base_url="http://localhost:8000/api")
    api.set_endpoint("/session/data")  # Default endpoint

    try:
        data = api.get()  # GET http://localhost:8000/api/session/data
        logger.info("GET default endpoint result: %s", data)
    except Exception as e:
        logger.exception("Failed GET default endpoint.")


# -------------------------------------------------------------------------
# Example 2: GET request with endpoint override and optional JSON payload
# -------------------------------------------------------------------------
def example_get_override_with_payload():
    """
    Perform a GET request while overriding the default endpoint and sending
    an optional JSON payload.

    Useful for APIs that support GET requests with JSON in the body.
    """
    api = get_api("ExampleAPI", base_url="http://localhost:8000/api")
    api.set_endpoint("/session/data")  # default endpoint

    payload = {
        "user": "Alice",
        "filter": "active"
    }

    try:
        # Overrides the default endpoint for this call and sends a JSON payload
        data = api.get("/session/latest", json=payload)
        logger.info("GET override endpoint with payload result: %s", data)
    except Exception as e:
        logger.exception("Failed GET override endpoint with payload.")


# -------------------------------------------------------------------------
# Example 3: POST request with JSON payload
# -------------------------------------------------------------------------
def example_post_json():
    """
    Send JSON data to the API using POST.
    """
    api = get_api("ExampleAPI", base_url="http://localhost:8000/api")
    api.set_endpoint("/session/data")

    payload = {
        "user_id": 123,
        "action": "start_session"
    }

    try:
        response = api.post(json=payload)
        logger.info("POST JSON response: %s", response)
    except Exception as e:
        logger.exception("Failed POST JSON request.")


# -------------------------------------------------------------------------
# Example 4: POST request with form data
# -------------------------------------------------------------------------
def example_post_form():
    """
    Send form-encoded data using POST.
    """
    api = get_api("ExampleAPI", base_url="http://localhost:8000/api")
    api.set_endpoint("/session/data")

    form_data = {
        "user_id": 123,
        "action": "stop_session"
    }

    try:
        response = api.post(data=form_data)
        logger.info("POST form response: %s", response)
    except Exception as e:
        logger.exception("Failed POST form request.")


# -------------------------------------------------------------------------
# Example 5: Reusing a client across multiple endpoints
# -------------------------------------------------------------------------
def example_reuse_client():
    """
    Demonstrates using a single ApiClient instance for multiple calls.
    """
    api = get_api("ExampleAPI", base_url="http://localhost:8000/api")

    try:
        api.set_endpoint("/session/data")
        result1 = api.get()
        logger.info("First GET result: %s", result1)

        # Change endpoint and reuse same client
        api.set_endpoint("/session/history")
        result2 = api.get()
        logger.info("Second GET result: %s", result2)

    except Exception as e:
        logger.exception("Failed reuse client example.")


# -------------------------------------------------------------------------
# Example 6: Create a client with a custom name and base URL (no API_CONFIG)
# -------------------------------------------------------------------------
def example_custom_client():
    """
    Demonstrates creating an ApiClient with a custom name and base URL
    without needing a predefined entry in API_CONFIG.

    Useful for one-off endpoints or dynamically configured services.
    """
    from shared.api.api_client import ApiClient

    # Instantiate client directly
    my_api = ApiClient(
        name="MyEndpoint",
        base_url="http://localhost:8000/api",
        headers={"Authorization": "Bearer mytoken"}
    )

    # Optional: set default endpoint
    my_api.set_endpoint("/session/data")

    try:
        # GET request using default endpoint
        result = my_api.get()
        logger.info("Custom client GET result: %s", result)

        # GET request with endpoint override and optional JSON payload
        payload = {"user": "Alice", "filter": "active"}
        result2 = my_api.get("/session/latest", json=payload)
        logger.info("Custom client GET with payload result: %s", result2)

    except Exception as e:
        logger.exception("Failed custom client example.")


# -------------------------------------------------------------------------
# Main Execution (for testing / demonstration)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    example_get_default_endpoint()
    example_get_override_endpoint()
    example_post_json()
    example_post_form()
    example_reuse_client()
