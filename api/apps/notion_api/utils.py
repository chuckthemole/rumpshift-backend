import os
import requests
import logging
from shared.utils.enums.notion import NotionAction
from shared.domain.CoffeeGrinder import CoffeeGrinder
from shared.Notion.notion_client import NotionClient

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = os.getenv("NOTION_VERSION")
NOTION_BASE_URL = "https://api.notion.com/v1/"


def send_to_notion(source: str, payload: dict, mode: str = "create_page", page_id: str = None):
    """
    Sends a log entry to Notion.
    Supports creating a new page or appending to an existing one.

    Args:
        source (str): The source of the log (e.g., coffee_grinder)
        payload (dict): Dictionary containing the data to log
        mode (str): 'append' or 'create_page'
        page_id (str): Notion page ID for append mode. Optional if mode=create_page.
    """

    # Instantiate the client upfront
    client = NotionClient(
        api_key=os.getenv("NOTION_API_KEY"),
        database_id=page_id or os.getenv("NOTION_LOG_PAGE_ID"),
        mode=mode
    )

    logger.info(client)

    # Default target ID from environment (for create_page parent or append page)
    default_target_id = os.getenv("NOTION_LOG_PAGE_ID")
    target_id = page_id or default_target_id

    if not target_id:
        logger.warning("No Notion target ID set, skipping")
        return None, {"error": "No Notion target ID"}

    # Prepare common content text
    content_text = f"Source: {source} | Payload: {payload}"

    # Headers
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    # --- APPEND MODE ---
    if client.mode == NotionAction.APPEND:
        url = f"{NOTION_BASE_URL}blocks/{target_id}/children"
        data = {
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content_text}}
                        ]
                    }
                }
            ]
        }
        try:
            response = requests.patch(url, headers=headers, json=data)
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Error appending to Notion: {e}")
            return None, {"error": str(e)}

    # --- CREATE PAGE MODE ---
    elif client.mode == NotionAction.CREATE_PAGE:
        url = f"{NOTION_BASE_URL}pages"
        data = {
            "parent": {"page_id": target_id},
            "properties": {
                "title": [
                    {"type": "text", "text": {"content": f"Log from {source}"}}
                ]
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content_text}}
                        ]
                    }
                }
            ]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return None, {"error": str(e)}

    # --- COFFEE ENTRY MODE ---
    elif client.mode == NotionAction.COFFEE_ENTRY:
        logger.info(payload)
        user = payload.get("user")
        duration = payload.get("duration")
        beans = payload.get("beans")
        status, result = CoffeeGrinder(
            notion_token=NOTION_API_KEY, database_id=page_id).add_coffee_entry(user, duration, beans)
        return status, result

    else:
        return None, {"error": f"Unsupported mode: {mode}"}
