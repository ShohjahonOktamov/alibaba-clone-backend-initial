import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestOrderHistoryView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, order_factory, order_item_factory, product_factory):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.product = product_factory(price=100)
        self.order1 = order_factory(user=self.user, status="completed")
        self.order2 = order_factory(user=self.user, status="pending")

        order_item_factory(order=self.order1, product=self.product, quantity=1)
        order_item_factory(order=self.order2, product=self.product, quantity=2)

        self.url = '/api/orders/history/'

    def test_order_history(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        assert len(response.data['results']) == 2
        assert response.data['results'][0]['status'] == 'pending'
        assert response.data['results'][1]['status'] == 'completed'

    def test_order_history_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_order_history_no_orders(self, tokens, api_client, user_factory):
        new_user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        new_user.groups.add(buyer_group)
        new_user.save()
        access, _ = tokens(new_user)
        client = api_client(token=access)

        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0
