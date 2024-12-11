from typing import Type

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import Category


class CategorySerializer(ModelSerializer):
    class Meta:
        model: Type[Category] = Category
        fields: tuple[str] = "id", "name", "icon", "is_active", "created_at", "parent", "children"

    children = SerializerMethodField(method_name="get_children")

    def get_children(self, obj: Category) -> list[dict[str, str | bool | list | None]]:
        return CategorySerializer(obj.children.all(), many=True)
