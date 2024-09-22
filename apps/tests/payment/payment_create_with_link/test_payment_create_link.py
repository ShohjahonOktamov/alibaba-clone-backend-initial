import pytest
from unittest.mock import patch
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestPaymentLinkView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user, status='pending', amount=100)
        self.url = "/payment/{id}/create/link/".format(id=self.order.id)

    @patch('stripe.checkout.Session.create')
    def test_payment_link_success(self, mock_create):
        mock_create.return_value = {
            'id': 'sess_123',
            'url': 'https://checkout.stripe.com/pay/sess_123'
        }

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert 'url' in response.data
        assert response.data['url'] == 'https://checkout.stripe.com/pay/sess_123'
        mock_create.assert_called_once()

        self.order.refresh_from_db()
        assert self.order.transaction_id == 'sess_123'

    def test_payment_link_canceled_order(self):
        self.order.status = 'canceled'
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Order already canceled.'

    def test_payment_link_order_already_paid(self):
        self.order.status = 'paid'
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Order cannot be updated.'

    def test_payment_link_order_shipped(self):
        self.order.status = 'shipped'
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Order cannot be updated.'

    def test_payment_link_order_delivered(self):
        self.order.status = 'delivered'
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Order cannot be updated.'

    def test_payment_link_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.patch(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_link_no_permission(self, api_client, tokens, user_factory):
        another_user = user_factory()
        access, _ = tokens(another_user)
        unauthorized_client = api_client(token=access)

        response = unauthorized_client.patch(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
