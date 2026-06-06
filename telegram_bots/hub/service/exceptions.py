from httpcore import NetworkError, Response

from http import HTTPStatus


class HTTPError(NetworkError):
    def __init__(self, response: Response) -> None:
        self.response = response
        super().__init__(HTTPStatus(response.status).description)
