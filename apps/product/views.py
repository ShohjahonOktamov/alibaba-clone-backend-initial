from typing import TYPE_CHECKING, Type

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import AllowAny

from .filters import CategoryFilter
from .models import Category
from .serializers import CategorySerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet


# Create your views here.

class RetrieveCategoryView(RetrieveAPIView):
    queryset: "QuerySet[Category]" = Category.objects.all()
    serializer_class: Type[CategorySerializer] = CategorySerializer
    permission_classes: tuple[Type[AllowAny]] = AllowAny,


class ListCategoriesView(ListAPIView):
    queryset: "QuerySet[Category]" = Category.objects.all()
    serializer_class: Type[CategorySerializer] = CategorySerializer
    permission_classes: tuple[Type[AllowAny]] = AllowAny,
    filterset_class: Type[CategoryFilter] = CategoryFilter
