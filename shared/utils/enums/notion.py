from enum import Enum


class NotionAction(Enum):
    COFFEE_ENTRY = "COFFEE_ENTRY"
    APPEND = "append"
    CREATE = "create"
    UPDATE = "update"
    CREATE_PAGE = "create_page"


class NotionConstants(Enum):
    BASE_URL = "https://api.notion.com/v1"
    VERSION = "2022-06-28"
    PAGE_ENDPOINT = "/pages"
    BLOCKS_ENDPOINT = "/blocks"
