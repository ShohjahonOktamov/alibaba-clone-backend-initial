import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestOrderDetailView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, order_factory, order_item_factory, product_factory):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.product = product_factory(price=100)
        self.order = order_factory(user=self.user, status="completed")
        order_item_factory(order=self.order, product=self.product, quantity=1)

        self.url = f'/api/orders/{self.order.pk}/'

    def test_order_detail(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_order_detail_404(self):
        response = self.client.get('/api/orders/1000/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_order_detail_unauthorized_user(self, api_client, tokens, user_factory):
        new_user = user_factory()
        access, _ = tokens(new_user)
        client = api_client(token=access)

        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_order_detail_unauthenticated(self, api_client):
        """Test that an unauthenticated user cannot access order details."""
        unauthenticated_client = api_client()
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
