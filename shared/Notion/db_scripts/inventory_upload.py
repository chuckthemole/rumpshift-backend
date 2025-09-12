#!/usr/bin/env python3
"""
inventory_upload.py

Script to upload an inventory list (from a JSON file) to a Notion database.

Features:
- Upload any JSON array as an inventory entry in a Notion database
- Columns: Name (string), Date Uploaded (date), Items (rich_text)

Usage:
    python inventory_upload.py --api_key <YOUR_NOTION_KEY> --db_id <DATABASE_ID> --file coffees.json --name coffees [--verbose]
"""

import requests
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

NOTION_VERSION = "2022-06-28"


def upload_inventory_entry(api_key: str, database_id: str, list_name: str, items: list, base_url: str = "https://api.notion.com/v1"):
    """Upload a list of items as a new entry in the Notion database."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    url = f"{base_url}/pages"

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": list_name}}]},
            "Date Uploaded": {"date": {"start": datetime.utcnow().isoformat()}},
            "Items": {"rich_text": [{"text": {"content": json.dumps(items)}}]}
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        logging.info(
            f"Uploaded inventory list '{list_name}' with {len(items)} items to database.")
    except requests.exceptions.RequestException as e:
        logging.error(
            f"Failed to upload inventory list: {e} - {resp.text if 'resp' in locals() else ''}")


def load_json_file(file_path: str) -> list:
    """Load items from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        logging.error(f"File not found: {file_path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                logging.error("JSON file must contain an array of items.")
                return []
            return data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON file: {e}")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload an inventory list to a Notion database."
    )
    parser.add_argument("--api_key", required=True,
                        help="Notion integration API key")
    parser.add_argument("--db_id", required=True,
                        help="Notion Database ID for inventory")
    parser.add_argument("--file", required=True,
                        help="Path to JSON file containing inventory list")
    parser.add_argument("--name", required=True,
                        help="Name of the inventory list")
    parser.add_argument("--base_url", default="https://api.notion.com/v1",
                        help="Base Notion API URL")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    items = load_json_file(args.file)
    if items:
        upload_inventory_entry(args.api_key, args.db_id,
                               args.name, items, args.base_url)
