import factory

from faker import Faker
from cart.models import Cart, CartItem

fake = Faker()


class CartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cart

    id = factory.Faker('pyint', min_value=1, max_value=100000)
    user = factory.SubFactory('tests.factories.user_factory.UserFactory')


class CartItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CartItem

    id = factory.Faker('pyint', min_value=1, max_value=100000)
    cart = factory.SubFactory('tests.factories.cart_factory.CartFactory')
    product = factory.SubFactory('tests.factories.product_factory.ProductFactory')
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
