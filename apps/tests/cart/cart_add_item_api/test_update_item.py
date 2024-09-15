import pytest
from rest_framework.test import APIClient
from rest_framework import status
from user.models import Group
from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestUpdateItemQuantityView:

    @pytest.fixture
    def setup(self, user_factory, product_factory, api_client, tokens):
        self.url = '/api/cart/update/'

        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()
        self.access, _ = tokens(self.user)
        self.client = api_client(self.access)
        self.product = product_factory.create(title='Test Product', price=100)
        self.cart, _ = Cart.objects.get_or_create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_update_item_quantity_success(self, setup):
        data = {
            'product_id': self.product.id,
            'quantity': 3
        }
        response = self.client.patch(self.url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        self.cart_item.refresh_from_db()
        assert self.cart_item.quantity == 3

    def test_update_item_quantity_invalid_product(self, setup):
        data = {
            'product_id': 999,
            'quantity': 3
        }
        response = self.client.patch(self.url, data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_item_quantity_invalid_quantity(self, setup):
        data = {
            'product_id': self.product.id,
            'quantity': 0
        }
        response = self.client.patch(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_item_quantity_unauthenticated(self, setup, api_client):
        client = api_client()
        data = {
            'product_id': 1,
            'quantity': 2
        }
        response = client.patch(self.url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
