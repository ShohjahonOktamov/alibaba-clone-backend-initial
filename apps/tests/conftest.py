import uuid

import pytest

from core import settings
from django.core.management import call_command
from faker import Faker
from pytest_factoryboy import register

try:
    from rest_framework.test import APIClient
except ImportError:
    pass

try:
    from rest_framework_simplejwt.tokens import RefreshToken
except ImportError:
    pass

if "user" in settings.INSTALLED_APPS:
    from tests.factories.user_factory import UserFactory

    register(UserFactory)

if "product" in settings.INSTALLED_APPS:
    from tests.factories.category_factory import CategoryFactory

    register(CategoryFactory)

if "product" in settings.INSTALLED_APPS:
    from tests.factories.product_factory import ProductFactory

    register(ProductFactory)

if "order" in settings.INSTALLED_APPS:
    from tests.factories.order_factory import OrderFactory, OrderItemFactory

    register(OrderFactory)
    register(OrderItemFactory)

if "cart" in settings.INSTALLED_APPS:
    from tests.factories.cart_factory import CartFactory, CartItemFactory

    register(CartFactory)
    register(CartItemFactory)

if "wishlist" in settings.INSTALLED_APPS:
    from tests.factories.wishlist_factory import WishlistFactory

    register(WishlistFactory)

if "notification" in settings.INSTALLED_APPS:
    from tests.factories.notification_factory import NotificationFactory

    register(NotificationFactory)

fake = Faker()


@pytest.fixture
def api_client():
    def _api_client(token=None):
        client = APIClient(raise_request_exception=False)
        if token:
            client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return client

    return _api_client


@pytest.fixture
def tokens():
    def _tokens(user):
        refresh = RefreshToken.for_user(user)
        access = str(getattr(refresh, 'access_token'))
        return access, refresh

    return _tokens


@pytest.fixture
def fake_number():
    def fake_number():
        country_code = '+99890'
        national_number = fake.numerify(text="#######")
        full_number = country_code + national_number
        return full_number

    return fake_number


@pytest.fixture
def fake_redis(request):
    import fakeredis
    fake_redis = fakeredis.FakeRedis()
    return fake_redis


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    try:
        with django_db_blocker.unblock():
            call_command('initial_data')
    except Exception as e:
        print(f"Failed to load initial data: {e}")
        pass


@pytest.fixture
def fake_uuid():
    return uuid.uuid4()
