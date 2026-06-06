from typing import TypedDict


class BotCredentials(TypedDict):
    id: int
    token: str
    webhook_url: str
