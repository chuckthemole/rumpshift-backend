import os
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from shared.logger.logger import get_logger

# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Notion configuration
# -----------------------------------------------------------------------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION")
NOTION_BASE_URL = "https://api.notion.com/v1/"


@extend_schema(
    summary="Query a Notion database",
    description=(
        "Fetches the content of a Notion database using its unique database ID. "
        "Optionally, you can specify an integration key by providing `integration` as a query parameter. "
        "If not provided, the default NOTION_API_KEY is used."
    ),
    parameters=[
        OpenApiParameter(
            name="db_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="The Notion database ID to query."
        ),
        OpenApiParameter(
            name="integration",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Optional environment variable name of the Notion API key to use."
        ),
    ],
    responses={
        200: {"description": "Successfully retrieved database content from Notion."},
        400: {"description": "Invalid Notion database ID."},
        401: {"description": "Unauthorized — check your Notion API key."},
        500: {"description": "Unexpected error when contacting Notion API."},
    },
)
@api_view(['GET'])
def get_notion_database(request, db_id):
    integration_name = request.query_params.get("integration")
    notion_api_key = os.getenv(
        integration_name) if integration_name else NOTION_API_KEY

    logger.debug(
        "get_notion_database called: db_id=%s, integration=%s", db_id, integration_name)

    if not notion_api_key:
        logger.error("No Notion API key found for integration: %s",
                     integration_name)
        return Response({"error": "Notion API key not found for the requested integration."}, status=400)

    url = f"{NOTION_BASE_URL}databases/{db_id}/query"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    try:
        logger.debug("Sending POST request to Notion: %s", url)
        response = requests.post(url, headers=headers)
        logger.debug("Notion response status: %s", response.status_code)
        return Response(response.json(), status=response.status_code)
    except Exception as e:
        logger.exception("Error querying Notion database %s", db_id)
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def search_notion_databases(request):
    logger.debug("search_notion_databases called")

    url = NOTION_BASE_URL + "search"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    data = {"filter": {"value": "database", "property": "object"}}

    try:
        response = requests.post(url, headers=headers, json=data)
        logger.debug("Notion search response status: %s", response.status_code)

        if response.status_code == 200:
            results = response.json().get("results", [])
            formatted = [
                {"id": db["id"], "title": get_title_from_db(db)} for db in results]
            logger.debug("Found %d databases", len(formatted))
            return Response(formatted)
        else:
            logger.error("Notion search failed: %s", response.text)
            return Response(response.json(), status=response.status_code)
    except Exception as e:
        logger.exception("Error searching Notion databases")
        return Response({"error": str(e)}, status=500)


def get_title_from_db(db_obj):
    try:
        title_prop = db_obj.get("title", [])
        if title_prop and isinstance(title_prop, list):
            return title_prop[0].get("plain_text", "")
    except Exception as e:
        logger.warning("Failed to extract title from database object: %s", e)
    return "(Untitled)"


@extend_schema(
    summary="List the block contents of a Notion page",
    description=(
        "Fetches the blocks/children inside a Notion page by its page ID. "
        "Optionally specify an integration key via ?integration=ENV_VAR_NAME. "
        "If omitted, uses the default NOTION_API_KEY."
    ),
    parameters=[
        OpenApiParameter(
            name="page_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="The Notion page ID to list contents for."
        ),
        OpenApiParameter(
            name="integration",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Optional environment variable name for a different Notion API key."
        ),
    ],
    responses={
        200: {"description": "Successfully retrieved the Notion page contents."},
        400: {"description": "Invalid or missing Notion API key."},
        401: {"description": "Unauthorized — Notion rejected API key."},
        500: {"description": "Unexpected backend or network error."},
    }
)
@api_view(['GET'])
def list_notion_page_contents(request, page_id):
    integration_name = request.query_params.get("integration")

    # Determine which key to use
    notion_api_key = os.getenv(
        integration_name) if integration_name else NOTION_API_KEY

    logger.debug(
        "list_notion_page_contents called: page_id=%s, integration=%s, resolved_key=%s",
        page_id,
        integration_name,
        "<default>" if not integration_name else integration_name
    )

    if not notion_api_key:
        logger.error(
            "No Notion API key available for integration '%s'", integration_name)
        return Response(
            {"error": "Notion API key not found for the requested integration."},
            status=400
        )

    url = f"{NOTION_BASE_URL}blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    logger.debug("Requesting Notion page blocks: GET %s", url)

    try:
        response = requests.get(url, headers=headers)
        logger.debug(
            "Notion response for page_id=%s — status=%s",
            page_id,
            response.status_code
        )

        # Success
        if response.status_code == 200:
            raw_json = response.json()
            blocks = raw_json.get("results", [])

            logger.debug("Page %s returned %d blocks", page_id, len(blocks))

            formatted = [
                {
                    "id": block["id"],
                    "type": block["type"],
                    "has_children": block.get("has_children", False)
                }
                for block in blocks
            ]

            return Response(formatted)

        # Notion returned an error
        logger.error(
            "Error from Notion listing page %s: %s",
            page_id,
            response.text
        )
        return Response(response.json(), status=response.status_code)

    except Exception as e:
        logger.exception(
            "Exception listing page contents for page_id=%s", page_id)
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_notion_page(request, page_id):
    integration_name = request.query_params.get("integration")
    notion_api_key = os.getenv(
        integration_name) if integration_name else NOTION_API_KEY

    if not notion_api_key:
        return Response({"error": "Missing API key"}, status=400)

    url = f"{NOTION_BASE_URL}pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            raw = response.json()

            props = raw.get("properties", {})

            # Turn Notion's rich property structure into simple output
            formatted = {}
            for k, v in props.items():
                if v["type"] == "rich_text":
                    formatted[k] = "".join([t["plain_text"]
                                           for t in v["rich_text"]])
                elif v["type"] == "title":
                    formatted[k] = "".join([t["plain_text"]
                                           for t in v["title"]])
                elif v["type"] == "number":
                    formatted[k] = v["number"]
                elif v["type"] == "date":
                    formatted[k] = v["date"]["start"] if v["date"] else None
                elif v["type"] == "select":
                    formatted[k] = v["select"]["name"] if v["select"] else None
                else:
                    formatted[k] = v

            return Response(formatted)

        return Response(response.json(), status=response.status_code)

    except Exception as e:
        logger.exception("Error fetching page")
        return Response({"error": str(e)}, status=500)


@extend_schema(
    summary="Update recipe inputs in Notion",
    description=(
        "Posts input values to a given Notion page (recipe) via its page ID in the path. "
        "Notion formulas will compute dependent values automatically."
    ),
    parameters=[
        OpenApiParameter(
            name="recipe_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="The Notion page ID for the recipe to update."
        ),
        OpenApiParameter(
            name="integration",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Optional environment variable name for a different Notion API key."
        ),
    ],
    request={
        "type": "object",
        "properties": {
            "inputs": {"type": "object"}
        },
        "required": ["inputs"]
    },
    responses={
        200: {"description": "Successfully updated the recipe in Notion."},
        400: {"description": "Missing or invalid inputs."},
        500: {"description": "Error updating recipe in Notion."},
    },
)
@api_view(['POST'])
def compute_recipe(request, recipe_id):
    """
    Updates the input fields of a recipe page in Notion.
    Dependent fields are automatically computed via Notion formulas.
    Supports specifying a custom integration key via query parameter.
    """
    try:
        # Determine which Notion API key to use
        integration_name = request.query_params.get("integration")
        notion_api_key = os.getenv(
            integration_name) if integration_name else NOTION_API_KEY

        if not notion_api_key:
            logger.error(
                "No Notion API key found for integration: %s", integration_name)
            return Response({"error": "Notion API key not found for the requested integration."}, status=400)

        inputs = request.data.get("inputs")
        if not inputs or not isinstance(inputs, dict):
            logger.error("Invalid inputs for recipe %s: %s",
                         recipe_id, request.data)
            return Response({"error": "Missing or invalid 'inputs' object"}, status=400)

        logger.debug("Updating Notion recipe %s with inputs: %s",
                     recipe_id, inputs)

        url = f"{NOTION_BASE_URL}pages/{recipe_id}"
        headers = {
            "Authorization": f"Bearer {notion_api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

        # Format inputs for Notion page update
        properties_payload = {}
        for key, value in inputs.items():
            # Convert empty string or None to null
            if value == "" or value is None:
                properties_payload[key] = {"number": None}  # default fallback
                continue

            # Detect if this is likely a date field
            if isinstance(value, str) and "-" in value and key.lower().endswith("date"):
                # Expecting ISO format for Notion date
                properties_payload[key] = {"date": {"start": value}}
            else:
                try:
                    # Attempt to treat as numeric
                    properties_payload[key] = {"number": float(value)}
                except (ValueError, TypeError):
                    logger.warning(
                        "Invalid value for field %s: %s, sending null instead", key, value
                    )
                    properties_payload[key] = {"number": None}

        payload = {"properties": properties_payload}

        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error("Failed updating Notion page %s: %s",
                         recipe_id, response.text)
            return Response(response.json(), status=response.status_code)

        logger.info("Successfully updated Notion recipe %s", recipe_id)
        return Response({"status": "success", "recipeId": recipe_id}, status=200)

    except Exception as e:
        logger.exception("Error updating Notion recipe %s", recipe_id)
        return Response({"error": str(e)}, status=500)
