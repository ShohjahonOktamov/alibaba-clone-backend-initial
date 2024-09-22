import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestPaymentCancelView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, order_factory, tokens):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.order = order_factory(user=self.user, status='pending')
        self.url = "/payment/{id}/cancel/".format(id=self.order.id)

    def test_payment_cancel_success(self):
        response = self.client.patch(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Order successfully canceled.'

        self.order.refresh_from_db()
        assert self.order.status == 'canceled'

    @pytest.mark.parametrize("initial_status, expected_status_code, expected_detail", [
        ('canceled', status.HTTP_400_BAD_REQUEST, 'Order already canceled.'),
        ('paid', status.HTTP_400_BAD_REQUEST, 'Order cannot be canceled.'),
        ('shipped', status.HTTP_400_BAD_REQUEST, 'Order cannot be canceled.'),
        ('delivered', status.HTTP_400_BAD_REQUEST, 'Order cannot be canceled.'),
    ])
    def test_payment_cancel_status_restrictions(self, initial_status, expected_status_code, expected_detail):
        self.order.status = initial_status
        self.order.save()

        response = self.client.patch(self.url)

        assert response.status_code == expected_status_code
        assert response.data['detail'] == expected_detail

    def test_payment_cancel_unauthenticated(self, api_client):
        unauthenticated_client = api_client()
        response = unauthenticated_client.patch(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_payment_cancel_no_permission(self, api_client, tokens, user_factory):
        another_user = user_factory()
        access, _ = tokens(another_user)
        unauthorized_client = api_client(token=access)

        response = unauthorized_client.patch(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
