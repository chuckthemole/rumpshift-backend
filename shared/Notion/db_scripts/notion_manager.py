#!/usr/bin/env python3
"""
notion_manager.py

Script to manage Notion databases under a specified page.

Features:
- Create a database with customizable properties
- List a database's properties
- Clear all entries in a database
- Delete a database
- Extendable for creating arbitrary pages

Usage:
    python notion_manager.py --api_key <YOUR_NOTION_KEY> --parent_page_id <PAGE_ID> [options]
"""

import json
import requests
import argparse
import logging
import sys

# ----------------------------
# Logging configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

NOTION_VERSION = "2022-06-28"


# ----------------------------
# Notion API helpers
# ----------------------------
def create_database(api_key: str, parent_page_id: str, title: str = "New Database",
                    properties: dict | None = None, base_url: str = "https://api.notion.com/v1"):
    """
    Create a Notion database under a parent page with customizable properties.

    Args:
        api_key: Notion API key
        parent_page_id: Page ID under which the database is created
        title: Name of the database
        properties: Optional dict mapping column names to types
                    e.g., {"User": "title", "Timestamp": "date", "Duration": "number"}
        base_url: Base Notion API URL
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    # Default columns if none provided
    if properties is None:
        properties = {
            "User": "title",
            "Timestamp": "date",
            "Duration": "number",
            "Beans": "rich_text"
        }

    # Convert user-provided types to Notion property objects
    notion_props = {}
    for name, prop_type in properties.items():
        if prop_type == "title":
            notion_props[name] = {"title": {}}
        elif prop_type == "number":
            notion_props[name] = {"number": {"format": "number"}}
        elif prop_type == "date":
            notion_props[name] = {"date": {}}
        elif prop_type == "rich_text":
            notion_props[name] = {"rich_text": {}}
        else:
            logging.warning(
                f"Unknown property type '{prop_type}' for column '{name}', skipping.")

    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": notion_props
    }

    url = f"{base_url}/databases"
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logging.info(
            f"Database '{title}' created successfully under page {parent_page_id}.")
        logging.info(f"Database ID: {data['id']}")
        return data
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error: {e} - {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")


def list_database_properties(api_key: str, database_id: str, base_url: str = "https://api.notion.com/v1"):
    """
    List the current properties of the database.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION
    }
    url = f"{base_url}/databases/{database_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        props = response.json().get("properties", {})
        logging.info(f"Database properties: {props}")
        return props
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get database properties: {e}")
        return {}


def clear_database_entries(api_key: str, database_id: str, base_url: str = "https://api.notion.com/v1"):
    """
    Archive all pages in a Notion database.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    # Fetch all pages in the database
    query_url = f"{base_url}/databases/{database_id}/query"
    try:
        response = requests.post(query_url, headers=headers, json={})
        response.raise_for_status()
        pages = response.json().get("results", [])
        logging.info(
            f"Found {len(pages)} pages to archive in database {database_id}.")

        for page in pages:
            page_id = page["id"]
            patch_url = f"{base_url}/pages/{page_id}"
            payload = {"archived": True}
            patch_resp = requests.patch(
                patch_url, headers=headers, json=payload)
            patch_resp.raise_for_status()
            logging.debug(f"Archived page {page_id}")
        logging.info("All pages archived successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to clear database: {e}")


def delete_database(api_key: str, database_id: str, base_url: str = "https://api.notion.com/v1"):
    """
    Delete a database by archiving it (Notion API does not support full deletion).
    This effectively removes it from visibility in Notion.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    patch_url = f"{base_url}/databases/{database_id}"
    payload = {"archived": True}

    try:
        response = requests.patch(patch_url, headers=headers, json=payload)
        response.raise_for_status()
        logging.info(f"Database {database_id} archived successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to delete database: {e}")


# ----------------------------
# CLI interface
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage Notion databases under a parent page."
    )
    parser.add_argument("--api_key", required=True, help="Notion API key")
    parser.add_argument("--parent_page_id",
                        help="Parent page ID for database creation")
    parser.add_argument("--title", default="New Database",
                        help="Database title")
    parser.add_argument("--properties", type=str, default=None,
                        help="JSON string of column names and types, e.g. '{\"User\": \"title\", \"Score\": \"number\"}'")
    parser.add_argument(
        "--clear_db_id", help="Database ID to clear all entries")
    parser.add_argument("--delete_db_id", help="Database ID to delete/archive")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle properties input
    props_dict = None
    if args.properties:
        try:
            props_dict = json.loads(args.properties)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON for --properties: {e}")
            sys.exit(1)

    # Execute actions
    if args.clear_db_id:
        clear_database_entries(args.api_key, args.clear_db_id)
    elif args.delete_db_id:
        delete_database(args.api_key, args.delete_db_id)
    elif args.parent_page_id:
        db_data = create_database(
            args.api_key, args.parent_page_id, args.title, props_dict)
        if db_data:
            list_database_properties(args.api_key, db_data["id"])
    else:
        logging.error(
            "No action specified. Provide --parent_page_id, --clear_db_id, or --delete_db_id.")
        sys.exit(1)
