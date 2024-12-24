from typing import TYPE_CHECKING, Type

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .filters import CategoryFilter
from .models import Category, Product
from .permissions import IsBuyer
from .serializers import CategorySerializer, ProductSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet


# Create your views here.

class RetrieveCategoryView(RetrieveAPIView):
    queryset: "QuerySet[Category]" = Category.objects.all()
    serializer_class: Type[CategorySerializer] = CategorySerializer
    permission_classes: tuple[Type[AllowAny]] = IsAuthenticated,


class ListCategoriesView(ListAPIView):
    queryset: "QuerySet[Category]" = Category.objects.all()
    serializer_class: Type[CategorySerializer] = CategorySerializer
    permission_classes: tuple[Type[AllowAny]] = IsAuthenticated,
    filterset_class: Type[CategoryFilter] = CategoryFilter


class ListCategoryProductsView(ListAPIView):
    serializer_class: Type[ProductSerializer] = ProductSerializer
    permission_classes: tuple[
        Type[AllowAny], Type[IsBuyer]] = IsAuthenticated, IsBuyer

    def get_queryset(self) -> "QuerySet[Product]":
        return Product.objects.filter(category=self.kwargs.get("pk"))
