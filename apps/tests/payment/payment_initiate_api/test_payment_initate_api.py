import pytest
from unittest.mock import patch
from rest_framework import status
from core import settings


@pytest.mark.order(1)
def test_payment_app_exists():
    app_name = 'payment'

    try:
        import payment  # noqa
    except ImportError:
        assert False, f"{app_name} app folder missing"


@pytest.mark.order(2)
def test_payment_app_created():
    assert "payment" in settings.INSTALLED_APPS, "payment app not installed"


@pytest.mark.order(3)
def test_stripe_exists():
    try:
        import stripe
    except ImportError:
        assert False, "Stripe is not installed."


@pytest.mark.order(4)
def test_stripe_keys_exist_in_settings():
    assert hasattr(settings, 'STRIPE_TEST_PUBLIC_KEY'), "STRIPE_TEST_PUBLIC_KEY is missing in settings."
    assert settings.STRIPE_TEST_PUBLIC_KEY, "STRIPE_TEST_PUBLIC_KEY is set but empty."
    assert hasattr(settings, 'STRIPE_TEST_SECRET_KEY'), "STRIPE_TEST_SECRET_KEY is missing in settings."
    assert settings.STRIPE_TEST_SECRET_KEY, "STRIPE_TEST_SECRET_KEY is set but empty."


@pytest.mark.order(5)
def test_stripe_keys_format():
    assert settings.STRIPE_TEST_PUBLIC_KEY.startswith('pk_test_'), "STRIPE_TEST_PUBLIC_KEY format is invalid."
    assert settings.STRIPE_TEST_SECRET_KEY.startswith('sk_test_'), "STRIPE_TEST_SECRET_KEY format is invalid."


@pytest.mark.order(6)
@pytest.mark.django_db
class TestPaymentCreateView:
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens):
        from user.models import Group

        user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        user.groups.add(buyer_group)
        user.save()

        self.user = user
        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user)

        self.url = "/api/payment/{id}/initiate/".format(id=self.order.id)

        self.valid_payload = {
            'card_number': '4242424242424242',
            'expiry_month': '12',
            'expiry_year': '2025',
            'cvc': '123'
        }

    @patch('stripe.PaymentIntent.create')
    @patch('stripe.PaymentIntent.retrieve')
    @pytest.mark.parametrize(
        "order_status, expected_status_code, expected_message",
        [
            (PENDING, status.HTTP_200_OK, None),
            (PAID, status.HTTP_400_BAD_REQUEST, 'Order is already paid.'),
            (SHIPPED, status.HTTP_400_BAD_REQUEST, 'Order has been shipped.'),
            (DELIVERED, status.HTTP_400_BAD_REQUEST, 'Order has been delivered.'),
            (CANCELED, status.HTTP_400_BAD_REQUEST, 'Order already canceled.')
        ]
    )
    def test_payment_create_for_different_order_statuses(self, mock_retrieve, mock_create, order_status,
                                                         expected_status_code, expected_message):
        mock_create.return_value = {'id': 'pi_12345'}
        mock_retrieve.return_value = {'client_secret': 'secret_12345'}

        self.order.status = order_status
        self.order.save()

        response = self.client.patch(self.url, data=self.valid_payload, format='json')

        assert response.status_code == expected_status_code

        if expected_message:
            assert response.data['detail'] == expected_message
        else:
            assert 'client_secret' in response.data
            assert response.data['client_secret'] == 'secret_12345'

    @pytest.mark.parametrize(
        "card_number, expiry_month, expiry_year, cvc",
        [
            ('', '12', '2025', '123'),
            ('4242424242424242', '', '2025', '123'),
            ('4242424242424242', '12', '', '123'),
            ('4242424242424242', '12', '2025', ''),
        ]
    )
    def test_payment_create_incomplete_card_details(self, card_number, expiry_month, expiry_year, cvc):
        incomplete_payload = {
            'card_number': card_number,
            'expiry_month': expiry_month,
            'expiry_year': expiry_year,
            'cvc': cvc
        }

        response = self.client.patch(self.url, data=incomplete_payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Card details are incomplete.'
