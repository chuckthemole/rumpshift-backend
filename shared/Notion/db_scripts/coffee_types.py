#!/usr/bin/env python3
"""
coffee_types.py

Script to manage a Notion page for "Coffee Types". 

Features:
- Upload coffee types from a JSON file (array of strings) as bulleted list items
- Optionally clear all existing items from the page
- View current page blocks

Usage:
    python coffee_types.py --api_key <YOUR_NOTION_KEY> --page_id <PAGE_ID> --file coffees.json [--clear] [--list] [--verbose]
"""

import requests
import argparse
import logging
import sys
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

NOTION_VERSION = "2022-06-28"


def list_page_blocks(api_key: str, page_id: str, base_url: str = "https://api.notion.com/v1"):
    """List the current child blocks of a Notion page."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION
    }
    url = f"{base_url}/blocks/{page_id}/children"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        blocks = response.json().get("results", [])
        logging.info("Current page blocks:")
        for block in blocks:
            text = block.get(block["type"], {}).get("text", [])
            if text:
                logging.info(f"- {text[0].get('plain_text', '')}")
        return blocks
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get page blocks: {e}")
        return []


def clear_page_blocks(api_key: str, page_id: str, base_url: str = "https://api.notion.com/v1"):
    """Archive all child blocks in a Notion page."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    url = f"{base_url}/blocks/{page_id}/children"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        blocks = response.json().get("results", [])
        logging.info(f"Found {len(blocks)} blocks to archive.")
        for block in blocks:
            block_id = block["id"]
            delete_url = f"{base_url}/blocks/{block_id}"
            delete_payload = {"archived": True}
            del_resp = requests.patch(
                delete_url, headers=headers, json=delete_payload)
            del_resp.raise_for_status()
            logging.info(f"Archived block {block_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to clear page: {e}")


def upload_coffee_types(api_key: str, page_id: str, coffees: list, base_url: str = "https://api.notion.com/v1"):
    """Upload coffee types as bulleted list items into the Notion page."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    url = f"{base_url}/blocks/{page_id}/children"

    blocks = []
    for coffee in coffees:
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "text": [{"type": "text", "text": {"content": coffee}}]
            }
        })

    payload = {"children": blocks}
    try:
        resp = requests.patch(url, headers=headers, json=payload)
        resp.raise_for_status()
        logging.info(f"Uploaded {len(coffees)} coffee types to page.")
    except requests.exceptions.RequestException as e:
        logging.error(
            f"Failed to upload coffees: {e} - {resp.text if 'resp' in locals() else ''}")


def load_coffee_file(file_path: str) -> list:
    """Load coffee types from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        logging.error(f"File not found: {file_path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                logging.error(
                    "JSON file must contain an array of coffee types (strings).")
                return []
            return data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON file: {e}")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage a Notion page for Coffee Types.")
    parser.add_argument("--api_key", required=True,
                        help="Notion integration API key")
    parser.add_argument("--page_id", required=True,
                        help="Notion Page ID to manage")
    parser.add_argument("--file", help="Path to JSON file with coffee types")
    parser.add_argument(
        "--base_url", default="https://api.notion.com/v1", help="Base Notion API URL")
    parser.add_argument("--clear", action="store_true",
                        help="Archive all existing blocks in the page")
    parser.add_argument("--list", action="store_true",
                        help="List current page blocks")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        list_page_blocks(args.api_key, args.page_id, args.base_url)

    if args.clear:
        clear_page_blocks(args.api_key, args.page_id, args.base_url)

    if args.file:
        coffees = load_coffee_file(args.file)
        if coffees:
            upload_coffee_types(args.api_key, args.page_id,
                                coffees, args.base_url)
