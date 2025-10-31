import os
from datetime import datetime, timezone
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ----------------------------
# Environment
# ----------------------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
NOTION_BASE_URL = "https://api.notion.com/v1/"
NOTION_LOG_DATABASE_ID = os.getenv("NOTION_LOG_DATABASE_ID")
NOTION_TEMP_LOG_DATABASE_ID = os.getenv("NOTION_TEMP_LOG_DATABASE_ID")


# ----------------------------
# Helper function: Convert values to Notion properties
# ----------------------------
def notion_property(value, prop_name=None):
    """
    Convert Python values to a Notion property object.
    Supports title, string, number, date.
    """
    if prop_name in ["User", "Entry"]:
        # Title property
        return {"title": [{"text": {"content": value}}]}
    elif isinstance(value, str):
        return {"rich_text": [{"text": {"content": value}}]}
    elif isinstance(value, (int, float)):
        return {"number": value}
    elif isinstance(value, dict) and "start" in value:
        return {"date": value}
    else:
        return {"rich_text": [{"text": {"content": str(value)}}]}


# ----------------------------
# API Endpoint
# ----------------------------
@api_view(['POST'])
def log_to_notion(request):
    """
    Log an entry to a Notion database.

    Expects JSON body:
    {
        "database_id": "<db_id>",
        "Count": <int>,
        "Start Timestamp": {"start": "ISO8601 string"},
        "End Timestamp": {"start": "ISO8601 string"},
        "User": "<string>",
        "Notes": "<string>"
    }

    Returns:
        JSON response from Notion API or error details.
    """
    data = request.data
    if not isinstance(data, dict):
        return Response({"error": "Invalid JSON payload."}, status=400)

    # Extract database_id
    db_id = data.pop("database_id", NOTION_LOG_DATABASE_ID)
    if not db_id:
        return Response({"error": "No database ID provided."}, status=400)

    # Validate start/end timestamps
    start_ts = data.get("Start Timestamp", {}).get("start")
    end_ts = data.get("End Timestamp", {}).get("start")

    if not start_ts or not end_ts:
        return Response({"error": "Start and End timestamps are required."}, status=400)

    try:
        # Parse ISO8601 timestamps
        start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_ts.replace("Z", "+00:00"))

        # Calculate duration in seconds (can be converted to minutes/hours if needed)
        duration_seconds = (end_dt - start_dt).total_seconds()
        data["Duration"] = round(duration_seconds, 2)  # round to 2 decimals
    except Exception as e:
        return Response({"error": f"Invalid timestamp format: {str(e)}"}, status=400)

    # Convert properties for Notion
    properties = {k: notion_property(v, k) for k, v in data.items()}

    payload = {
        "parent": {"database_id": db_id},
        "properties": properties
    }

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{NOTION_BASE_URL}pages", headers=headers, json=payload)
        response.raise_for_status()
        return Response({"status": "ok", "data": response.json()})
    except requests.exceptions.HTTPError as e:
        return Response({
            "status": "error",
            "error": str(e),
            "response": response.text
        }, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return Response({"status": "error", "error": str(e)}, status=500)


# ----------------------------
# API Endpoint for Arduino temp logs
# ----------------------------
@api_view(['POST'])
def log_to_notion_temp(request):
    """
    Log a temperature entry to a Notion database (Arduino format).

    Expected payload:
    {
        "database_id": "<db_id>",       # optional
        "Temperature (C)": 23.4,        # number
        "Timestamp": "ISO8601 string",  # date
        "Entry": "TempLog"              # optional, title
    }

    Notes:
    - Only send properties that exist in your Notion DB.
    - 'Entry' must be the title property.
    - 'Timestamp' must be a date property.
    """
    data = request.data
    if not isinstance(data, dict):
        return Response({"error": "Invalid JSON payload."}, status=400)

    db_id = data.pop("database_id", NOTION_TEMP_LOG_DATABASE_ID)
    if not db_id:
        return Response({"error": "No database ID provided."}, status=400)

    # Ensure title property exists
    entry = data.get("Entry", "TempLog")
    data["Entry"] = entry

    # Ensure Timestamp exists
    timestamp_str = data.get("Timestamp")
    if not timestamp_str:
        timestamp_str = datetime.now(timezone.utc).isoformat(
            timespec='seconds').replace("+00:00", "Z")

    # Convert Timestamp to Notion date object
    data["Timestamp"] = {"start": timestamp_str}

    # Convert properties
    properties = {k: notion_property(v, k) for k, v in data.items()}

    payload = {"parent": {"database_id": db_id}, "properties": properties}

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{NOTION_BASE_URL}pages", headers=headers, json=payload)
        response.raise_for_status()
        return Response({"status": "ok", "data": response.json()})
    except requests.exceptions.HTTPError as e:
        return Response(
            {"status": "error", "error": str(e), "response": response.text},
            status=response.status_code,
        )
    except requests.exceptions.RequestException as e:
        return Response({"status": "error", "error": str(e)}, status=500)
