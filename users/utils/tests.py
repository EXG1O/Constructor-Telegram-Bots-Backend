from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import User

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rest_framework.views import AsView
else:
    AsView = Any


def assert_view_requires_terms_acceptance(
    view: AsView[Any], request: Request, user: User, **view_kwargs: Any
) -> None:
    user.accepted_terms = False

    response: Response = view(request, **view_kwargs)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    user.accepted_terms = True
