from uuid import uuid4

from django.db.models import Model, UUIDField, CharField, TextField, DateField, ForeignKey, ManyToManyField, \
    DecimalField, IntegerField, BinaryField, ImageField, BooleanField, CASCADE


# Create your models here.

class Category(Model):
    class Meta:
        verbose_name: str = "Category"
        verbose_name_plural: str = "Categories"

    id = UUIDField(primary_key=True, default=uuid4())
    name = CharField(max_length=255)
    icon = ImageField(null=True, blank=True)
    is_active = BooleanField(default=True)
    description = TextField(null=True)
    parent = ForeignKey(to="self", on_delete=CASCADE, null=True, related_name="children")
    created_at = DateField(auto_now_add=True)
    updated_at = DateField(auto_now=True)


class Color(Model):
    id = UUIDField(primary_key=True, default=uuid4())
    name = CharField(max_length=255)
    hex_value = TextField(null=True)


class Size(Model):
    id = UUIDField(primary_key=True, default=uuid4())
    name = CharField(max_length=255)
    description = TextField(null=True)


class Product(Model):
    id = UUIDField(primary_key=True, default=uuid4())
    seller = ForeignKey(to="user.User", on_delete=CASCADE)
    name = CharField(max_length=255)
    description = TextField(null=True)
    colors = ManyToManyField(to=Color, blank=True)
    sizes = ManyToManyField(to=Size, blank=True)
    price = DecimalField(max_digits=10, decimal_places=2)
    quantity = IntegerField(default=0)
    category_id = ForeignKey(to=Category, on_delete=CASCADE)
    created_at = DateField(auto_now_add=True)
    updated_at = DateField(auto_now=True)


class Image(Model):
    id = UUIDField(primary_key=True, default=uuid4())
    product_id = ForeignKey(to=Product, on_delete=CASCADE)
    image = BinaryField()
    created_at = DateField(auto_now_add=True)
