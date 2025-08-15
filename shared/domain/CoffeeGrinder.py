import os
import requests
from datetime import datetime
from ..utils.enums.notion import NotionConstants


class CoffeeGrinder:
    def __init__(self, notion_token: str, database_id: str):
        self.notion_token = notion_token
        self.database_id = database_id
        self.api_url = NotionConstants.BASE_URL.value + \
            NotionConstants.PAGE_ENDPOINT.value
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": NotionConstants.VERSION.value,
            "Content-Type": "application/json",
        }

    def add_coffee_entry(self, user: str, duration: int, beans: str):
        """Append a new coffee grinding entry to the Notion database.

        Returns:
            tuple: (status_code, response_json) where status_code is int and
                response_json is the parsed JSON or error info.
        """
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                # Use title property for User
                "Name": {"title": [{"text": {"content": user}}]},
                "Timestamp": {"date": {"start": datetime.utcnow().isoformat()}},
                "Duration": {"number": duration},
                "Beans": {"rich_text": [{"text": {"content": beans}}]},
            },
        }

        try:
            response = requests.post(
                self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx
            return response.status_code, response.json()
        except requests.exceptions.HTTPError:
            return response.status_code, {"error": response.text}
        except requests.exceptions.RequestException as e:
            return None, {"error": str(e)}
