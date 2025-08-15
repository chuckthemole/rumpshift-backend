import os
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Load Notion credentials from environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION")
NOTION_BASE_URL = "https://api.notion.com/v1/"
# Optional: default log database
NOTION_LOG_DATABASE_ID = os.getenv("NOTION_LOG_DATABASE_ID")


@api_view(['POST'])
def log_to_notion(request, source):
    """
    Relay an Arduino log message to a Notion database.

    URL Param:
        source (str): Identifier of the device sending the log, e.g., 'coffee_grinder'.

    Request Body (JSON):
        Arbitrary log data. Will automatically include the 'source' field.

    Returns:
        JSON response from Notion or error details.
    """
    try:
        # Parse the incoming JSON from Arduino
        payload = request.data
    except Exception:
        return Response({"error": "Invalid JSON payload"}, status=400)

    # Add the source to the payload
    payload["source"] = source

    # Build request headers for Notion
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    print('In log.py:::' + payload)

    # Construct the URL for adding a new page to the log database
    url = f"{NOTION_BASE_URL}pages"

    # Format payload as a new Notion page (simple example with a 'properties'
