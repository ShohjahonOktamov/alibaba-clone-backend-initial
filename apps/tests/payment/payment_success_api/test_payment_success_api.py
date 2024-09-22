import pytest
from unittest.mock import patch
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestPaymentSuccessView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user, status='pending', transaction_id='sess_123')
        self.url = "/payment/{id}/success/".format(id=self.order.id)

    @patch('stripe.checkout.Session.retrieve')
    def test_payment_success_update(self, mock_retrieve):
        mock_retrieve.return_value = {
            'payment_status': 'paid'
        }

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Order updated successfully.'

        # Verify that the order status has been updated
        self.order.refresh_from_db()
        assert self.order.status == 'paid'
        assert self.order.is_paid is True

    @pytest.mark.parametrize("initial_status, expected_status_code, expected_detail", [
        ('paid', status.HTTP_400_BAD_REQUEST, 'Order cannot be updated.'),
        ('shipped', status.HTTP_400_BAD_REQUEST, 'Order cannot be updated.'),
        ('delivered', status.HTTP_400_BAD_REQUEST, 'Order cannot be updated.'),
    ])
    def test_payment_success_order_status_restrictions(self, initial_status, expected_status_code, expected_detail):
        self.order.status = initial_status
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == expected_status_code
        assert response.data['detail'] == expected_detail

    def test_payment_success_missing_transaction_id(self):
        self.order.transaction_id = None
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Transaction ID is missing.'

    @patch('stripe.checkout.Session.retrieve')
    def test_payment_success_payment_failed(self, mock_retrieve):
        mock_retrieve.return_value = {
            'payment_status': 'unpaid'
        }

        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Payment failed.'

    def test_payment_success_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.patch(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_success_no_permission(self, api_client, tokens, user_factory):
        another_user = user_factory()
        access, _ = tokens(another_user)
        unauthorized_client = api_client(token=access)

        response = unauthorized_client.patch(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
