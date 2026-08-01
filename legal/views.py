from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.mixins import RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from .models import Document
from .serializers import DocumentSerializer


@method_decorator(cache_page(3600), name='dispatch')
class DocumentViewSet(RetrieveModelMixin, GenericViewSet[Document]):
    authentication_classes = []
    permission_classes = []
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    lookup_field = 'type'
