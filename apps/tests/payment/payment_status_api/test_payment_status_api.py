import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestPaymentStatusView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user, status='pending')
        self.url = "/api/payment/{id}/status/".format(id=self.order.id)

    def test_payment_status_success(self):
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == self.order.status

    def test_payment_status_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_status_no_permission(self, api_client, tokens, user_factory):
        another_user = user_factory()
        access, _ = tokens(another_user)
        unauthorized_client = api_client(token=access)

        response = unauthorized_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_payment_status_order_not_found(self, api_client):
        non_existent_order_id = 9999
        url = "/api/payment/{id}/status/".format(id=non_existent_order_id)

        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
