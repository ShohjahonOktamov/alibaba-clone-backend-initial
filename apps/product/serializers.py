from typing import Type

from rest_framework.serializers import ModelSerializer, CharField, SerializerMethodField

from .models import Category, Product


class CategorySerializer(ModelSerializer):
    class Meta:
        model: Type[Category] = Category
        fields: tuple[str] = "id", "name", "icon", "is_active", "created_at", "parent", "children"

    children = SerializerMethodField(method_name="get_children")

    def get_children(self, obj: Category) -> list[dict[str, str | bool | list | None]]:
        return CategorySerializer(obj.children.all(), many=True).data


class ProductSerializer(ModelSerializer):
    class Meta:
        model: Type[Product] = Product
        fields: tuple[str] = "id", "category", "seller", "title", "description", "price", "image", "quantity"

    category = CategorySerializer()
    seller = SerializerMethodField(method_name="get_seller")
    image = CharField(source="image.image.url")

    def get_seller(self, obj) -> dict[str, str]:
        seller = obj.seller

        return {
            "id": seller.id,
            "first_name": seller.first_name,
            "last_name": seller.last_name,
            "phone_number": seller.phone_number,
            "email": seller.email,
            "gender": seller.gender
        }
