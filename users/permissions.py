from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import User

from typing import cast


class IsTermsAccepted(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = cast(User | None, request.user)
        return bool(user and user.accepted_terms)
