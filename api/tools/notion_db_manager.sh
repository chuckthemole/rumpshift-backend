#!/bin/bash
#
# notion_db_manager.sh
#
# Utility for managing Notion databases.
#
# Features:
#   - Create a database under a specified parent page
#   - Delete (archive) a database by ID
#
# Usage:
#   ./notion_db_manager.sh create "<DB_TITLE>" <PROPERTIES_JSON_OR_FILE>
#   ./notion_db_manager.sh delete <DATABASE_ID>
#   ./notion_db_manager.sh help
#
# Examples:
#   ./notion_db_manager.sh create "Temperature Logs" db_props.json
#   ./notion_db_manager.sh delete 1234abcd5678efgh9012ijkl3456mnop
#

# ----------------------------
# Load environment variables
# ----------------------------
ENV_FILE="$(dirname "$0")/../.env"

export NOTION_API_KEY=$(grep '^NOTION_API_KEY=' "$ENV_FILE" | cut -d '=' -f2-)
export NOTION_LOG_PAGE=$(grep '^NOTION_LOG_PAGE=' "$ENV_FILE" | cut -d '=' -f2-)

# ----------------------------
# Fail fast if vars missing
# ----------------------------
if [ -z "$NOTION_API_KEY" ] || [ -z "$NOTION_LOG_PAGE" ]; then
  echo "Missing NOTION_API_KEY or NOTION_LOG_PAGE in $ENV_FILE"
  exit 1
fi

# ----------------------------
# Script locations
# ----------------------------
PYTHON_SCRIPT="$(dirname "$0")/../../shared/Notion/db_scripts/notion_manager.py"

# ----------------------------
# Helper: print usage
# ----------------------------
usage() {
  echo "Usage:"
  echo "  $0 create \"<DB_TITLE>\" <PROPERTIES_JSON_OR_FILE>"
  echo "  $0 delete <DATABASE_ID>"
  echo "  $0 help"
  echo
  echo "Examples:"
  echo "  $0 create \"Temperature Logs\" '{\"Entry\":\"title\",\"Value\":\"number\"}'"
  echo "  $0 create \"Patient Data\" ./db_props.json"
  echo "  $0 delete abcd1234efgh5678ijkl9012mnop3456"
}

# ----------------------------
# Command dispatch
# ----------------------------
ACTION=$1
shift

case "$ACTION" in
  create)
    DB_TITLE="$1"
    PROPS_INPUT="$2"

    if [ -z "$DB_TITLE" ] || [ -z "$PROPS_INPUT" ]; then
      echo "Missing arguments."
      usage
      exit 1
    fi

    # If PROPS_INPUT is a file, read contents; otherwise assume JSON string
    if [ -f "$PROPS_INPUT" ]; then
      DB_PROPERTIES=$(cat "$PROPS_INPUT")
    else
      DB_PROPERTIES="$PROPS_INPUT"
    fi

    echo "📗 Creating database '$DB_TITLE' under page $NOTION_LOG_PAGE..."
    python3 "$PYTHON_SCRIPT" \
      --api_key "$NOTION_API_KEY" \
      --parent_page_id "$NOTION_LOG_PAGE" \
      --title "$DB_TITLE" \
      --properties "$DB_PROPERTIES" \
      --verbose
    ;;

  delete)
    DB_ID=$1
    if [ -z "$DB_ID" ]; then
      echo "Missing database ID."
      usage
      exit 1
    fi
    echo "🗑️ Deleting database $DB_ID..."
    python3 "$PYTHON_SCRIPT" \
      --api_key "$NOTION_API_KEY" \
      --delete_db_id "$DB_ID" \
      --verbose
    ;;

  help|--help|-h)
    usage
    ;;

  *)
    echo "Unknown command: $ACTION"
    usage
    exit 1
    ;;
esac
