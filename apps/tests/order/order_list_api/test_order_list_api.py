import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestOrderListView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, order_factory, order_item_factory, product_factory):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.product1 = product_factory(price=100)
        self.product2 = product_factory(price=150)

        self.order1 = order_factory(user=self.user, status="completed")
        self.order2 = order_factory(user=self.user, status="pending")

        order_item_factory(order=self.order1, product=self.product1, quantity=1)
        order_item_factory(order=self.order2, product=self.product2, quantity=2)

        self.url = '/api/orders/'

    def test_order_list_authenticated(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['status'] == 'pending'
        assert response.data['results'][1]['status'] == 'completed'

        assert 'order_items' in response.data['results'][0]

        assert len(response.data['results'][0]['order_items']) == 1
        assert len(response.data['results'][1]['order_items']) == 1

    def test_order_list_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_order_list_no_orders(self, tokens, api_client, user_factory):
        new_user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        new_user.groups.add(buyer_group)
        new_user.save()
        access, _ = tokens(new_user)
        client = api_client(token=access)

        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0

    def test_order_list_no_permission(self, tokens, api_client, user_factory):
        new_user = user_factory()
        access, _ = tokens(new_user)
        client = api_client(token=access)

        response = client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
