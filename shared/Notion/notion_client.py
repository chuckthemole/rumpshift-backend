from ..utils.enums.notion import NotionAction

class NotionClient:
    def __init__(self, api_key: str, database_id: str, mode: str = "create_page"):
        self.api_key = api_key
        self.database_id = database_id
        # Normalize mode: uppercase, strip whitespace, match Enum
        cleaned_mode = mode.strip().upper()
        if cleaned_mode in NotionAction.__members__:
            self.mode = NotionAction[cleaned_mode]
        else:
            self.mode = NotionAction.CREATE_PAGE  # default
        print(f"Using mode: {self.mode}")

    def __str__(self):
        masked_key = self.api_key[:4] + "..." + \
            self.api_key[-4:] if self.api_key else "None"
        return f"NotionClient(mode={self.mode.value}, database_id={self.database_id}, api_key={masked_key})"

    # optional: also a __repr__ for better debug in interactive shells
    def __repr__(self):
        return self.__str__()
