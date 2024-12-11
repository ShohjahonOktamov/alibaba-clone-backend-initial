from typing import TYPE_CHECKING, Type

from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category
from .filters import CategoryFilter
from .serializers import CategorySerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request


# Create your views here.

class GetCategoryView(RetrieveModelMixin, ListModelMixin, GenericAPIView):
    queryset: "QuerySet[Category]" = Category.objects.all()
    serializer_class: Type[CategorySerializer] = CategorySerializer
    authentication_classes: tuple[Type[AllowAny]] = AllowAny,

    def get(self, request: "Request", *args, **kwargs) -> Response:
        if "pk" in kwargs:
            return self.retrieve(request=request, *args, **kwargs)
        return self.list(request=request, *args, **kwargs)
