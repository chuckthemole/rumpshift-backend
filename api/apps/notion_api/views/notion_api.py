import os
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

# Load the Notion API token and (optionally) a default database ID from environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION")
NOTION_BASE_URL = "https://api.notion.com/v1/"


@extend_schema(
    summary="Query a Notion database",
    description=(
        "Fetches the content of a Notion database using its unique database ID. "
        "This endpoint acts as a proxy to the Notion API's `/databases/{db_id}/query` endpoint. "
        "Requires that your NOTION_API_KEY and NOTION_VERSION are correctly configured."
    ),
    parameters=[
        OpenApiParameter(
            name="db_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="The Notion database ID to query."
        ),
    ],
    responses={
        200: {
            "description": "Successfully retrieved database content from Notion.",
            "examples": [
                OpenApiExample(
                    "Sample Notion database response",
                    summary="Example Notion data",
                    value={
                        "object": "list",
                        "results": [
                            {"object": "page", "id": "page_id_1", "properties": {
                                "Name": {"title": [{"text": {"content": "Task A"}}]}}},
                            {"object": "page", "id": "page_id_2", "properties": {
                                "Name": {"title": [{"text": {"content": "Task B"}}]}}},
                        ]
                    },
                ),
            ],
        },
        400: {"description": "Invalid Notion database ID."},
        401: {"description": "Unauthorized — check your Notion API key."},
        500: {"description": "Unexpected error when contacting Notion API."},
    },
)
@api_view(['GET'])
def get_notion_database(request, db_id):
    """
    Query a Notion database by its ID and return its content.

    Params:
        db_id (str): The Notion database ID to query.

    Returns:
        JSON response with database content.
    """
    url = f"{NOTION_BASE_URL}databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",  # Use secure token
        # API version must match the version your integration supports
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    # Notion requires a POST even for querying databases
    response = requests.post(url, headers=headers)

    # Pass through the raw response from Notion
    return Response(response.json(), status=response.status_code)


@api_view(['GET'])
def search_notion_databases(request):
    """
    Use Notion's search endpoint to find all databases accessible to the integration.

    Returns:
        A filtered list of database IDs and their titles.
    """
    print('search_notion_databases')  # TODO: Remove or replace with proper logging before deploying

    url = NOTION_BASE_URL + "search"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    # Filter the search to only return databases
    data = {
        "filter": {
            "value": "database",
            "property": "object"
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        results = response.json().get("results", [])

        # Extract only ID and title from each database
        formatted = [
            {
                "id": db["id"],
                "title": get_title_from_db(db)
            }
            for db in results
        ]
        return Response(formatted)
    else:
        # If an error occurs, pass through the original Notion response
        return Response(response.json(), status=response.status_code)


def get_title_from_db(db_obj):
    """
    Helper function to extract the plain-text title from a Notion database object.

    Params:
        db_obj (dict): A Notion database object from the API.

    Returns:
        str: The extracted plain-text title or a fallback.
    """
    try:
        title_prop = db_obj.get("title", [])
        if title_prop and isinstance(title_prop, list):
            return title_prop[0].get("plain_text", "")
    except Exception:
        # In case Notion schema changes or malformed input
        pass
    return "(Untitled)"


@api_view(['GET'])
def list_notion_page_contents(request, page_id):
    """
    List the blocks (children) contained within a Notion page or block.

    Params:
        page_id (str): The ID of the page or block to query.

    Returns:
        List of block metadata (ID, type, has_children).
    """
    url = f"{NOTION_BASE_URL}blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        results = response.json().get("results", [])

        # Extract relevant data from each block
        formatted = [
            {
                "id": block["id"],
                "type": block["type"],
                "has_children": block.get("has_children", False)
            }
            for block in results
        ]
        return Response(formatted)
    else:
        # Forward any API errors from Notion
        return Response(response.json(), status=response.status_code)
