import pytest
from rest_framework import status
from core import settings


@pytest.mark.order(1)
def test_cart_app_created():
    assert "cart" in settings.INSTALLED_APPS, "cart app not installed"


@pytest.mark.order(2)
def test_cart_app_exists():
    app_name = 'cart'

    try:
        import cart  # noqa
    except ImportError:
        assert False, f"{app_name} app folder missing"
    assert app_name in settings.INSTALLED_APPS, f"{app_name} app not installed"


@pytest.mark.order(3)
def test_cart_model_created():
    """
    The function tests that the articles model is created.
    """
    try:
        from cart.models import Cart  # noqa
    except ImportError:
        assert False, f"Cart model missing"

    try:
        from cart.models import CartItem  # noqa
    except ImportError:
        assert False, f"CartItem model missing"


@pytest.mark.django_db
class TestCartViews:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, product_factory):
        from cart.models import Cart, CartItem
        from user.models import Group

        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.url_get_items = '/api/cart/'
        self.url_add_item = '/api/cart/add/'

        self.product1 = product_factory(title="product1", price=10.12, quantity=10)
        self.product2 = product_factory(title="product2", price=20.43, quantity=20)

        self.cart = Cart.objects.create(user=self.user)
        self.cart_item1 = CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        self.cart_item2 = CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

    def test_get_items_view_authenticated(self):
        response = self.client.get(self.url_get_items)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert any(item['product']['title'] == 'product1' for item in response.data)
        assert any(item['product']['title'] == 'product2' for item in response.data)

    @pytest.mark.parametrize("endpoint, expected_status", [
        ('/api/cart/add/', status.HTTP_401_UNAUTHORIZED),
        ('/api/cart/add/', status.HTTP_401_UNAUTHORIZED),
    ])
    def test_unauthenticated_access(self, api_client, endpoint, expected_status):
        client = api_client()
        response = client.get(endpoint) if 'get' in endpoint else client.post(endpoint, {
            'product_id': str(self.product1.id),
            'quantity': 3
        })
        assert response.status_code == expected_status

    @pytest.mark.parametrize("quantity, expected_quantity", [
        (3, 3),
        (1, 1),
        (9, 9),
    ])
    def test_add_item_view_authenticated(self, quantity, expected_quantity):
        response = self.client.post(self.url_add_item, {
            'product_id': str(self.product1.id),
            'quantity': quantity
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data[1]['quantity'] == expected_quantity

    def test_add_item_view_insufficient_stock(self):
        response = self.client.post(self.url_add_item, {
            'product_id': str(self.product2.id),
            'quantity': 999
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    @pytest.mark.parametrize("endpoint, data, expected_status", [
        ('/api/cart/add/', {'quantity': 3}, status.HTTP_400_BAD_REQUEST),
        ('/api/cart/add/', {'product_id': "123"}, status.HTTP_400_BAD_REQUEST),
        ('/api/cart/add/', {'product_id': 'invalid-id', 'quantity': 3}, status.HTTP_400_BAD_REQUEST),
    ])
    def test_add_item_view_missing_or_invalid_data(self, endpoint, data, expected_status):
        client = self.client
        response = client.post(endpoint, data)
        assert response.status_code == expected_status
