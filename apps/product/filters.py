from typing import Type, TYPE_CHECKING

from django.db.models import Q
from django_filters import FilterSet, CharFilter

from .models import Category

if TYPE_CHECKING:
    from django.db.models import QuerySet


class CategoryFilter(FilterSet):
    class Meta:
        model: Type[Category] = Category
        include: tuple[str] = "name",

    search = CharFilter(method="filter_search")

    def filter_search(self, queryset: "QuerySet[Category]", name: str, value: str) -> "QuerySet[Category]":
        return queryset.filter(
            Q(name_icontains=value) |
            Q(parent_name_icontains=value)
        ).distinct()
