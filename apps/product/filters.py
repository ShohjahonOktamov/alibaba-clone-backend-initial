from typing import Type, TYPE_CHECKING

from django.db.models import Q
from django_filters import FilterSet, CharFilter

from .models import Category

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CategoryFilter(FilterSet):
    class Meta:
        model: Type[Category] = Category
        fields: list[str] = ["search"]

    search = CharFilter(method="filter_search", label="search")

    @staticmethod
    def filter_search(queryset: "QuerySet[Category]", name: str, value: str) -> "QuerySet[Category]":
        return queryset.filter(
            Q(name__icontains=value) |
            Q(parent__name__icontains=value)
        ).distinct()
