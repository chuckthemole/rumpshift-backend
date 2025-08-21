"""
Amazon Connect Flow Manager

This script provides CLI tools to manage Amazon Connect contact flows:
- List flows
- Download flows to local JSON files (with versioning)
- Upload edited flows back to Connect
- Create new flows

Directory structure:
cloud/aws/connect/flows/
    ├── __init__.py
    ├── flow_manager.py
    └── flows/           # downloaded JSON files

Usage examples:
1. List flows:
    python flow_manager.py list --instance-id <INSTANCE_ID> --profile <AWS_PROFILE>

2. Download all flows:
    python flow_manager.py download --instance-id <INSTANCE_ID> --profile <AWS_PROFILE>

3. Upload a flow:
    python flow_manager.py upload --instance-id <INSTANCE_ID> --flow-id <FLOW_ID> \
        --file flows/MyFlow.json --profile <AWS_PROFILE>

4. Create a new flow:
    python flow_manager.py create --instance-id <INSTANCE_ID> --name "NewFlow" \
        --type CONTACT_FLOW --file flows/NewFlow.json --profile <AWS_PROFILE>
"""

import boto3
import argparse
import os
import shutil
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_PROFILE = os.getenv("AWS_PROFILE")
DEFAULT_INSTANCE_ID = os.getenv("CONNECT_INSTANCE_ID")

# Default folder for storing flow JSON files
FLOWS_DIR = os.path.join(os.path.dirname(__file__), "flows")
ARCHIVE_DIR = os.path.join(FLOWS_DIR, "archive")


def init_dirs():
    """Ensure flows and archive directories exist."""
    os.makedirs(FLOWS_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def list_flows(instance_id, profile=None):
    """List all contact flows in the specified Amazon Connect instance."""
    session = boto3.Session(profile_name=profile)
    client = session.client("connect")
    paginator = client.get_paginator("list_contact_flows")

    print(f"Listing flows for instance {instance_id}:")
    for page in paginator.paginate(InstanceId=instance_id):
        for flow in page["ContactFlowSummaryList"]:
            flow_name = flow.get('Name', '<Unnamed>')
            flow_id = flow.get('Id', '<NoId>')
            flow_type = flow.get('Type', '<Unknown>')  # <-- safe fallback
            print(f"- {flow_name} (Id: {flow_id}, Type: {flow_type})")


def download_flows(instance_id, profile=None):
    """
    Download all contact flows from Connect instance to local JSON files.
    Previous versions are archived with timestamps.
    """
    init_dirs()
    session = boto3.Session(profile_name=profile)
    client = session.client("connect")
    paginator = client.get_paginator("list_contact_flows")

    for page in paginator.paginate(InstanceId=instance_id):
        for flow in page["ContactFlowSummaryList"]:
            flow_id = flow["Id"]
            flow_name = flow["Name"].replace(" ", "_")
            path = os.path.join(FLOWS_DIR, f"{flow_name}.json")

            # Archive previous version if exists
            if os.path.exists(path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.move(path, os.path.join(
                    ARCHIVE_DIR, f"{flow_name}_{timestamp}.json"))

            details = client.describe_contact_flow(
                InstanceId=instance_id, ContactFlowId=flow_id
            )
            content = details["ContactFlow"]["Content"]

            with open(path, "w") as f:
                f.write(content)

            print(f"Downloaded: {flow_name} → {path}")


def upload_flow(instance_id, flow_id, file_path, profile=None):
    """Upload a local JSON file to update an existing Connect flow."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path) as f:
        content = f.read()

    session = boto3.Session(profile_name=profile)
    client = session.client("connect")
    client.update_contact_flow_content(
        InstanceId=instance_id,
        ContactFlowId=flow_id,
        Content=content
    )
    print(f"Uploaded {file_path} → flow {flow_id}")


def create_flow(instance_id, name, flow_type, file_path, profile=None):
    """Create a new Connect contact flow from a local JSON file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path) as f:
        content = f.read()

    session = boto3.Session(profile_name=profile)
    client = session.client("connect")
    response = client.create_contact_flow(
        InstanceId=instance_id,
        Name=name,
        Type=flow_type,
        Content=content
    )
    new_id = response["Id"]
    print(f"Created new flow '{name}' with ID: {new_id}")


def main():
    parser = argparse.ArgumentParser(description="Amazon Connect Flow Manager")
    parser.add_argument(
        "--profile", help="AWS CLI profile to use (defaults to AWS_PROFILE in .env)", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    list_parser = subparsers.add_parser("list", help="List all flows")
    list_parser.add_argument(
        "--instance-id", help="Connect instance ID (defaults to CONNECT_INSTANCE_ID in .env)", default=None)

    # download
    download_parser = subparsers.add_parser(
        "download", help="Download all flows")
    download_parser.add_argument(
        "--instance-id", help="Connect instance ID (defaults to CONNECT_INSTANCE_ID in .env)", default=None)

    # upload
    upload_parser = subparsers.add_parser("upload", help="Upload a flow")
    upload_parser.add_argument(
        "--instance-id", help="Connect instance ID (defaults to CONNECT_INSTANCE_ID in .env)", default=None)
    upload_parser.add_argument("--flow-id", required=True)
    upload_parser.add_argument("--file", required=True)

    # create
    create_parser = subparsers.add_parser("create", help="Create a new flow")
    create_parser.add_argument(
        "--instance-id", help="Connect instance ID (defaults to CONNECT_INSTANCE_ID in .env)", default=None)
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument(
        "--type", choices=["CONTACT_FLOW", "CUSTOMER_QUEUE", "RULE"], default="CONTACT_FLOW")
    create_parser.add_argument("--file", required=True)

    args = parser.parse_args()

    # Use CLI args if provided, otherwise fall back to environment variables
    profile = args.profile or DEFAULT_PROFILE
    instance_id = getattr(args, "instance_id", None) or DEFAULT_INSTANCE_ID

    if not profile:
        raise ValueError(
            "AWS profile must be provided via --profile or AWS_PROFILE env var.")
    if not instance_id:
        raise ValueError(
            "Connect instance ID must be provided via --instance-id or CONNECT_INSTANCE_ID env var.")

    if args.command == "list":
        list_flows(instance_id, profile=profile)
    elif args.command == "download":
        download_flows(instance_id, profile=profile)
    elif args.command == "upload":
        upload_flow(instance_id, args.flow_id, args.file, profile=profile)
    elif args.command == "create":
        create_flow(instance_id, args.name, args.type,
                    args.file, profile=profile)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
