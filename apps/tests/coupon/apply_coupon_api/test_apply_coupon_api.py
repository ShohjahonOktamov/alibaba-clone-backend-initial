import pytest
from rest_framework import status
from coupon.models import Coupon
from user.models import Group
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4


@pytest.mark.django_db
class TestApplyCouponView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens, order_factory, cart_factory, cart_item_factory, product_factory):
        """Setup common variables for each test."""
        self.user = user_factory()
        seller_group = Group.objects.get(name="seller")
        self.user.groups.add(seller_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.url = '/api/coupons/apply/'

        self.order = order_factory(user=self.user, status='pending')

        self.cart = cart_factory(user=self.user)

        product = product_factory()
        self.cart_item = cart_item_factory(cart=self.cart, product=product, quantity=1)

    def create_coupon(self, code="DISCOUNT10", valid_from=None, valid_until=None, max_uses=10):
        """Helper method to create a coupon."""
        now = timezone.now()
        if valid_from is None:
            valid_from = now - timedelta(days=1)
        if valid_until is None:
            valid_until = now + timedelta(days=30)

        return Coupon.objects.create(
            created_by=self.user,
            code=code,
            discount_type='percentage',
            discount_value=10,
            valid_from=valid_from,
            valid_until=valid_until,
            max_uses=max_uses
        )

    def test_apply_coupon_success(self):
        """Test that a valid coupon can be applied successfully."""
        coupon = self.create_coupon(code="DISCOUNT10", valid_from=timezone.now() - timedelta(days=1),
                                    valid_until=timezone.now() + timedelta(days=30))

        data = {
            "coupon_code": coupon.code,
            "order_id": self.order.id
        }

        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK

    def test_apply_coupon_invalid_coupon(self):
        """Test applying an invalid coupon returns an error."""
        data = {
            "coupon_code": "INVALIDCOUPON",
            "order_id": self.order.id
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Coupon does not exist." in response.data['coupon_code']

    def test_apply_coupon_order_not_found(self):
        """Test that applying a coupon to a non-existing order returns a 404 error."""
        coupon = self.create_coupon(code="DISCOUNT10")
        invalid_order_id = uuid4()

        data = {
            "coupon_code": coupon.code,
            "order_id": invalid_order_id
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_apply_coupon_already_used(self):
        """Test that a user cannot apply a coupon they have already used."""
        coupon = self.create_coupon(code="DISCOUNT10")

        data = {
            "coupon_code": coupon.code,
            "order_id": self.order.id
        }
        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_200_OK

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_apply_coupon_expired(self):
        """Test applying an expired coupon returns an error."""
        coupon = self.create_coupon(code="DISCOUNT10", valid_until=timezone.now() - timedelta(days=1))

        data = {
            "coupon_code": coupon.code,
            "order_id": self.order.id
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['coupon_code'] == ['The coupon code has expired.']

    def test_apply_coupon_not_yet_valid(self):
        """Test applying a coupon that is not yet valid returns an error."""
        coupon = self.create_coupon(code="FUTURECOUPON", valid_from=timezone.now() + timedelta(days=1))

        data = {
            "coupon_code": coupon.code,
            "order_id": self.order.id
        }

        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['coupon_code'] == ['The coupon code is not yet valid.']
