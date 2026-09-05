from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from constructor_telegram_bots.mixins import IDLookupMixin
from users.models import User

from ..authentication import TokenAuthentication
from ..serializers import UserSerializer


class UserViewSet(IDLookupMixin, CreateModelMixin, GenericViewSet[User]):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
