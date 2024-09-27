import pytest
from rest_framework import status
from core import settings


@pytest.mark.order(1)
def test_orders_app_created():
    assert "order" in settings.INSTALLED_APPS, "order app not installed"


@pytest.mark.order(2)
def test_orders_app_exists():
    app_name = 'order'

    try:
        import order  # noqa
    except ImportError:
        assert False, f"{app_name} app folder missing"
    assert app_name in settings.INSTALLED_APPS, f"{app_name} app not installed"


@pytest.mark.order(3)
def test_order_model_created():
    """
    The function tests that the articles model is created.
    """
    try:
        from order.models import Order  # noqa
    except ImportError:
        assert False, f"Order model missing"

    try:
        from order.models import OrderItem  # noqa
    except ImportError:
        assert False, f"OrderItem model missing"


@pytest.mark.django_db
class TestCheckoutCreateView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, cart_factory, cart_item_factory, product_factory):
        from user.models import Group

        user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        user.groups.add(buyer_group)
        user.save()

        self.user = user
        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.product1 = product_factory(price=100)
        self.product2 = product_factory(price=200)
        self.cart = cart_factory(user=self.user)
        cart_item_factory(cart=self.cart, product=self.product1, quantity=1)
        cart_item_factory(cart=self.cart, product=self.product2, quantity=2)

        self.data = {
            "payment_method": "card",
            "country_region": "Uzbekistan",
            "city": "New York",
            "state_province_region": "NY",
            "postal_zip_code": "10001",
            "telephone_number": "1234567890",
            "address_line_1": "123 Test St",
            "address_line_2": "Apt 1"
        }

        self.url = '/api/orders/checkout/'

    def test_checkout_create_success(self):
        response = self.client.post(self.url, data=self.data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'pending'
        assert response.data['payment_method'] == 'card'
        assert response.data['country_region'] == 'Uzbekistan'
        assert len(response.data['order_items']) == 2

    @pytest.mark.parametrize("missing_field", [
        "payment_method",
        "country_region",
        "city",
        "state_province_region",
        "postal_zip_code",
        "telephone_number",
        "address_line_1"
    ])
    def test_checkout_create_missing_required_fields(self, missing_field):
        self.data.pop(missing_field)

        response = self.client.post(self.url, data=self.data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert missing_field in response.data

    @pytest.mark.parametrize("empty_field", [
        "payment_method",
        "country_region",
        "city",
        "state_province_region",
        "postal_zip_code",
        "telephone_number",
        "address_line_1"
    ])
    def test_checkout_create_empty_fields(self, empty_field):
        self.data[empty_field] = ''

        response = self.client.post(self.url, data=self.data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert empty_field in response.data

    def test_checkout_create_unconfirmed_order(self, order_factory):
        order_factory(user=self.user, status='pending')
        response = self.client.post(self.url, data=self.data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_checkout_create_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.post(self.url, data=self.data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_checkout_create_no_permission(self, tokens, api_client, user_factory, cart_factory, cart_item_factory):
        user = user_factory()
        cart = cart_factory(user=user)
        cart_item_factory(cart=cart, product=self.product1, quantity=1)

        access, _ = tokens(user)
        unauthorized_client = api_client(access)

        response = unauthorized_client.post(self.url, data=self.data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
