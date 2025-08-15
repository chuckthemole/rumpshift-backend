#!/usr/bin/env python3
"""
coffee_grinder.py

Script to manage a Notion database for "Coffee Grinder" logs. 

Features:
- Add standard properties (User, Timestamp, Duration, Beans)
- Optionally clear all existing entries
- View current database properties

Usage:
    python coffee_grinder.py --api_key <YOUR_NOTION_KEY> --db_id <DATABASE_ID> [--clear] [--list] [--verbose]
"""

import requests
import argparse
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

NOTION_VERSION = "2022-06-28"


def update_database_properties(api_key: str, database_id: str, base_url: str = "https://api.notion.com/v1"):
    """Add standard properties to the Notion database."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    properties_payload = {
        "properties": {
            "User": {"title": {}},
            "Timestamp": {"date": {}},
            "Duration": {"number": {"format": "number"}},
            "Beans": {"rich_text": {}}
        }
    }

    url = f"{base_url}/databases/{database_id}"
    logging.info(
        f"Updating database {database_id} with standard properties...")
    try:
        response = requests.patch(
            url, headers=headers, json=properties_payload)
        response.raise_for_status()
        logging.info("Database properties updated successfully!")
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error: {e} - {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")


def list_database_properties(api_key: str, database_id: str, base_url: str = "https://api.notion.com/v1"):
    """List the current properties of the database."""
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
    """Delete all entries from the database. Note: Notion API does not allow bulk delete, must update each page."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    # Get all pages
    url_query = f"{base_url}/databases/{database_id}/query"
    try:
        response = requests.post(url_query, headers=headers, json={})
        response.raise_for_status()
        pages = response.json().get("results", [])
        logging.info(f"Found {len(pages)} entries to delete.")
        for page in pages:
            page_id = page["id"]
            delete_url = f"{base_url}/pages/{page_id}"
            delete_payload = {"archived": True}
            del_resp = requests.patch(
                delete_url, headers=headers, json=delete_payload)
            del_resp.raise_for_status()
            logging.info(f"Archived page {page_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to clear database: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage a Notion database for Coffee Grinder logs.")
    parser.add_argument("--api_key", required=True,
                        help="Notion integration API key")
    parser.add_argument("--db_id", required=True,
                        help="Notion Database ID to manage")
    parser.add_argument(
        "--base_url", default="https://api.notion.com/v1", help="Base Notion API URL")
    parser.add_argument("--clear", action="store_true",
                        help="Archive all existing entries in the database")
    parser.add_argument("--list", action="store_true",
                        help="List current database properties")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        list_database_properties(args.api_key, args.db_id, args.base_url)

    if args.clear:
        clear_database_entries(args.api_key, args.db_id, args.base_url)

    update_database_properties(args.api_key, args.db_id, args.base_url)
