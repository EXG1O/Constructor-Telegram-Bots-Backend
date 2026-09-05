from .service.client import Client


class PlatformBot:
    is_authenticated = True

    def get_client(self) -> Client:
        return Client()
