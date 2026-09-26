from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from .enums import DocumentType
from .models import Document
from .serializers import DocumentSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            enum=DocumentType.values,
            location=OpenApiParameter.PATH,
        )
    ]
)
@method_decorator(cache_page(3600), name='dispatch')
class DocumentViewSet(RetrieveModelMixin, GenericViewSet[Document]):
    authentication_classes = []
    permission_classes = []
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    lookup_field = 'type'
