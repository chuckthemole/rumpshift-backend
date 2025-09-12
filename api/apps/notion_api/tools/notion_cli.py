#!/usr/bin/env python3
"""
notion_cli.py

Command-line tool to test Notion API endpoints via your Django backend.
Supports creating, clearing, and deleting databases, as well as running the Coffee Grinder script.

Usage examples:
    python notion_cli.py --create --title TEST
    python notion_cli.py --create --title TEST --properties-file log_basic.json
    python notion_cli.py --clear --db_id 264cee7d24dc81a888cfc449fe41ac3d
    python notion_cli.py --delete --db_id 264cee7d24dc81a888cfc449fe41ac3d
    python notion_cli.py --coffee --action list
"""

import argparse
import subprocess
import json
import sys
import os

BASE_URL = "http://localhost:8000/api/notion"  # Update if different
HEADERS = ["-H", "Content-Type: application/json"]


def run_curl(data: dict, endpoint: str):
    """
    Run a curl command to the Django API endpoint with JSON payload.
    """
    cmd = ["curl", "-X", "POST",
           f"{BASE_URL}/{endpoint}/"] + HEADERS + ["-d", json.dumps(data)]
    print("Running command:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Error executing curl:", e)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Test Notion API endpoints via curl")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true",
                       help="Create a new database under Log page")
    group.add_argument("--clear", action="store_true",
                       help="Clear a database by ID")
    group.add_argument("--delete", action="store_true",
                       help="Delete a database by ID")
    group.add_argument("--coffee", action="store_true",
                       help="Run Coffee Grinder script")

    parser.add_argument("--db_id", type=str,
                        help="Database ID for clear/delete")
    parser.add_argument("--title", type=str, help="Title for new database")
    parser.add_argument("--properties", type=str,
                        help="JSON string of properties for new database, e.g. '{\"User\":\"title\",\"Score\":\"number\"}'")
    parser.add_argument("--properties-file", type=str,
                        help="Path to JSON file containing properties")
    parser.add_argument("--action", type=str, default="list",
                        help="Action for Coffee Grinder: list, clear, update")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    data = {}
    if args.verbose:
        data["verbose"] = True

    # -----------------
    # Create database
    # -----------------
    if args.create:
        if args.title:
            data["title"] = args.title

        # Load properties from file if specified
        if args.properties_file:
            if not os.path.exists(args.properties_file):
                print(f"ERROR: File not found: {args.properties_file}")
                sys.exit(1)
            try:
                with open(args.properties_file, "r") as f:
                    data["properties"] = json.load(f)
            except json.JSONDecodeError as e:
                print("Invalid JSON in properties file:", e)
                sys.exit(1)
        # Otherwise parse inline JSON string
        elif args.properties:
            try:
                data["properties"] = json.loads(args.properties)
            except json.JSONDecodeError as e:
                print("Invalid JSON for properties:", e)
                sys.exit(1)

        run_curl(data, "create-log-database")

    # -----------------
    # Clear database
    # -----------------
    elif args.clear:
        if not args.db_id:
            print("ERROR: --db_id is required for --clear")
            sys.exit(1)
        data["db_id"] = args.db_id
        run_curl(data, "clear-database")

    # -----------------
    # Delete database
    # -----------------
    elif args.delete:
        if not args.db_id:
            print("ERROR: --db_id is required for --delete")
            sys.exit(1)
        data["db_id"] = args.db_id
        run_curl(data, "delete-database")

    # -----------------
    # Coffee Grinder
    # -----------------
    elif args.coffee:
        data["action"] = args.action
        run_curl(data, "run-coffee-grinder-script")


if __name__ == "__main__":
    main()
