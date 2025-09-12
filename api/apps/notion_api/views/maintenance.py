import os
import subprocess
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response

# ----------------------------
# Environment and constants
# ----------------------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION")
NOTION_LOG_PAGE_ID = os.getenv("NOTION_LOG_PAGE")
NOTION_BASE_URL = "https://api.notion.com/v1/"
NOTION_LOG_DATABASE_ID = os.getenv("NOTION_LOG_DATABASE_ID")
PYTHON_VERSION = "python3"

# Check essential environment variables
if not NOTION_API_KEY:
    print("ERROR: NOTION_API_KEY is missing!")
if not NOTION_LOG_DATABASE_ID:
    print("WARNING: NOTION_LOG_DATABASE_ID is missing!")
if not NOTION_LOG_PAGE_ID:
    print("WARNING: NOTION_LOG_PAGE_ID is missing!")

# Paths to scripts
COFFEE_GRINDER_SCRIPT = os.path.join(
    os.path.dirname(__file__),
    "../../../../shared/Notion/db_scripts/coffee_grinder.py"
)
NOTION_MANAGER_SCRIPT = os.path.join(
    os.path.dirname(__file__),
    "../../../../shared/Notion/db_scripts/notion_manager.py"
)


# ----------------------------
# Helper function
# ----------------------------
def run_script(cmd):
    """
    Executes a script via subprocess and returns a JSON-friendly response.
    """
    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        return {"status": "ok", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr.strip()}


# ----------------------------
# Coffee Grinder Endpoints
# ----------------------------
@api_view(['POST'])
def run_coffee_grinder_script(request):
    """
    Run the Coffee Grinder maintenance script against the configured Notion database.
    Actions: list, clear, update
    """
    action = request.data.get("action", "list")
    verbose = request.data.get("verbose", False)

    cmd = [PYTHON_VERSION, COFFEE_GRINDER_SCRIPT, "--api_key",
           NOTION_API_KEY, "--db_id", NOTION_LOG_DATABASE_ID]

    if action == "list":
        cmd.append("--list")
    elif action == "clear":
        cmd.append("--clear")
    elif action == "update":
        pass
    else:
        return Response({"error": f"Invalid action '{action}'"}, status=400)

    if verbose:
        cmd.append("--verbose")

    return Response(run_script(cmd))


# ----------------------------
# Notion Manager Endpoints
# ----------------------------
@api_view(['POST'])
def run_notion_manager_script(request):
    """
    Run the Notion Manager script to create a new database under a specified page.
    Accepts optional 'properties' for columns.
    """
    parent_page_id = request.data.get("parent_page_id")
    title = request.data.get("title", "New Database")
    verbose = request.data.get("verbose", False)
    properties = request.data.get(
        "properties", {"Duration": "number", "Timestamp": "date"})

    if not parent_page_id:
        return Response({"error": "Missing 'parent_page_id'"}, status=400)

    cmd = [
        PYTHON_VERSION,
        NOTION_MANAGER_SCRIPT,
        "--api_key", NOTION_API_KEY,
        "--parent_page_id", parent_page_id,
        "--title", title,
        "--properties", json.dumps(properties)
    ]

    if verbose:
        cmd.append("--verbose")

    return Response(run_script(cmd))


@api_view(['POST'])
def create_log_database(request):
    """
    Shortcut endpoint to create a new database under the Log page.
    Accepts optional 'properties' for columns.
    """
    if not NOTION_LOG_PAGE_ID:
        return Response({"error": "NOTION_LOG_PAGE_ID is not configured"}, status=500)

    title = request.data.get("title", "New Database")
    verbose = request.data.get("verbose", False)
    properties = request.data.get(
        "properties", {"Duration": "number", "Timestamp": "date"})

    cmd = [
        PYTHON_VERSION,
        NOTION_MANAGER_SCRIPT,
        "--api_key", NOTION_API_KEY,
        "--parent_page_id", NOTION_LOG_PAGE_ID,
        "--title", title,
        "--properties", json.dumps(properties)
    ]

    if verbose:
        cmd.append("--verbose")

    return Response(run_script(cmd))


# ----------------------------
# Clear and Delete Endpoints
# ----------------------------
@api_view(['POST'])
def clear_database(request):
    """
    Archive all entries in a database by ID.
    """
    db_id = request.data.get("db_id")
    verbose = request.data.get("verbose", False)

    if not db_id:
        return Response({"error": "Missing 'db_id'"}, status=400)

    cmd = [
        PYTHON_VERSION,
        NOTION_MANAGER_SCRIPT,
        "--api_key", NOTION_API_KEY,
        "--clear_db_id", db_id
    ]
    if verbose:
        cmd.append("--verbose")

    return Response(run_script(cmd))


@api_view(['POST'])
def delete_database(request):
    """
    Delete a database by ID using Notion Manager script.
    """
    db_id = request.data.get("db_id")
    verbose = request.data.get("verbose", False)

    if not db_id:
        return Response({"error": "Missing 'db_id'"}, status=400)

    cmd = [
        PYTHON_VERSION,
        NOTION_MANAGER_SCRIPT,
        "--api_key", NOTION_API_KEY,
        "--delete_db_id", db_id
    ]

    if verbose:
        cmd.append("--verbose")

    return Response(run_script(cmd))
