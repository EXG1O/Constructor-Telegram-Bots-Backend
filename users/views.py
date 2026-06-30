from django.core.files.storage import default_storage
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from constructor_telegram_bots.permissions import ReadOnly

from .authentication import JWTAuthentication
from .backends import TelegramBackend
from .jwt.tokens import AccessToken, RefreshToken
from .models import Token, User
from .permissions import IsTermsAccepted
from .serializers import (
    TokenSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserTokenRefreshSerializer,
)
from .utils.auth import user_login, user_logout, user_logout_all
from .utils.storage import get_user_file_names

from typing import cast
import base64
import hashlib
import secrets


class StatsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    @method_decorator(cache_page(3600))
    def get(self, request: Request) -> Response:
        return Response({'total': User.objects.count()})


class UserViewSet(RetrieveModelMixin, DestroyModelMixin, GenericViewSet[User]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self) -> User:
        return cast(User, self.request.user)

    @action(
        detail=False,
        methods=['POST'],
        url_path='login-init',
        authentication_classes=[],
        permission_classes=[],
    )
    def login_init(self, request: Request) -> Response:
        code_verifier: str = secrets.token_urlsafe(32)
        code_challenge: str = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip('=')
        )

        request.session['telegram_login_code_verifier'] = code_verifier

        return Response({'code_challenge': code_challenge})

    @action(
        detail=False, methods=['POST'], authentication_classes=[], permission_classes=[]
    )
    def login(self, request: Request) -> Response:
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User | None = TelegramBackend().authenticate(
            request,
            code=serializer.validated_data['code'],
            redirect_uri=serializer.validated_data['redirect_uri'],
            raise_exception=True,
        )

        if not user:
            raise AuthenticationFailed()

        refresh_token: RefreshToken = user_login(request, user)

        return Response(
            {
                'refresh_token': str(refresh_token),
                'access_token': str(refresh_token.access_token),
            }
        )

    @action(detail=True, methods=['POST'])
    def logout(self, request: Request, pk: str | None = None) -> Response:
        jwt_token = cast(AccessToken, request.auth)
        user_logout(request, jwt_token)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], url_path='logout-all')
    def logout_all(self, request: Request, pk: str | None = None) -> Response:
        user: User = self.get_object()
        user_logout_all(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        url_path='token-refresh',
        authentication_classes=[],
        permission_classes=[],
    )
    def token_refresh(self, request: Request, pk: str | None = None) -> Response:
        serializer = UserTokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token: RefreshToken = serializer.validated_data['refresh_token']

        return Response({'access_token': str(refresh_token.access_token)})

    @action(detail=True, methods=['POST'], url_path='accept-terms')
    def accept_terms(self, request: Request, pk: str | None = None) -> Response:
        user: User = self.get_object()
        user.accepted_terms = True
        user.terms_accepted_date = timezone.now()
        user.save(update_fields=['accepted_terms', 'terms_accepted_date'])

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, user: User) -> None:
        file_names: set[str] = get_user_file_names(user)

        user_logout_all(self.request, user)
        super().perform_destroy(user)

        for file_name in file_names:
            default_storage.delete(file_name)


class TokenViewSet(ReadOnlyModelViewSet[Token]):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated & (IsTermsAccepted | ReadOnly)]
    serializer_class = TokenSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering = ['-created_date']
    lookup_field = 'jti'

    def get_queryset(self) -> QuerySet[Token]:
        tokens: QuerySet[Token] = cast(User, self.request.user).tokens.all()

        if self.action in ('list', 'retrieve'):
            return tokens.select_related('blacklisted')

        return tokens
