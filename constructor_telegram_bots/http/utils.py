def build_user_agent(*data: str) -> str:
    return f'ConstructorTelegramBots ({"; ".join(["constructor.exg1o.org", *data])})'
