import pytest
from unittest.mock import patch
from rest_framework import status
import stripe
from user.models import Group


@pytest.mark.django_db
class TestPaymentConfirmView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens, cart_factory, cart_item_factory, product_factory):
        user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        user.groups.add(buyer_group)
        user.save()

        self.user = user
        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user, status='pending', transaction_id='pi_12345')
        self.url = "/api/payment/{id}/confirm/".format(id=self.order.id)

        self.cart = cart_factory(user=self.user)
        product1 = product_factory()
        cart_item_factory(cart=self.cart, product=product1)

    @patch('stripe.PaymentIntent.confirm')
    def test_payment_confirm_success(self, mock_confirm):
        mock_confirm.return_value = {'status': 'succeeded'}

        payload = {
            'client_secret': 'secret_12345'
        }

        response = self.client.patch(self.url, data=payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.data
        assert response.data['status'] == 'succeeded'
        mock_confirm.assert_called_once_with(self.order.transaction_id)

        self.order.refresh_from_db()
        assert self.order.status == 'paid'
        assert self.cart.items.count() == 0

    def test_payment_confirm_invalid_order_status(self):
        self.order.status = 'completed'
        self.order.save()

        payload = {
            'client_secret': 'secret_12345'
        }

        response = self.client.patch(self.url, data=payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Order payment status cannot be updated.'

    @patch('stripe.PaymentIntent.confirm')
    def test_payment_confirm_invalid_transaction_id(self, mock_confirm):
        mock_confirm.side_effect = stripe.error.InvalidRequestError(
            message="Invalid transaction ID", param="transaction_id"
        )

        payload = {
            'client_secret': 'secret_12345'
        }

        response = self.client.patch(self.url, data=payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert response.data['error'] == 'Invalid transaction ID'

    @patch('stripe.PaymentIntent.confirm')
    def test_payment_confirm_stripe_error(self, mock_confirm):
        mock_confirm.side_effect = stripe.error.StripeError("Stripe error")
        payload = {
            'client_secret': 'secret_12345'
        }

        response = self.client.patch(self.url, data=payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert response.data['error'] == 'Stripe error'

    def test_payment_confirm_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        payload = {
            'client_secret': 'secret_12345'
        }

        response = unauthenticated_client.patch(self.url, data=payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_confirm_no_permission(self, api_client, tokens, user_factory):
        another_user = user_factory()
        access, _ = tokens(another_user)
        unauthorized_client = api_client(token=access)

        payload = {
            'client_secret': 'secret_12345'
        }

        response = unauthorized_client.patch(self.url, data=payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
