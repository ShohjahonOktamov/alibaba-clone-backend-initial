import pytest
from rest_framework import status
from coupon.models import Coupon
from user.models import Group
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
class TestCouponDeleteUpdateView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens):
        """Setup common variables for each test."""
        self.user = user_factory()
        seller_group = Group.objects.get(name="seller")
        self.user.groups.add(seller_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.url = '/api/coupons/'

    def create_coupon(self, code="DISCOUNT10", discount_type='percentage', discount_value=10, active=True):
        """Helper method to create a coupon."""
        return Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30),
            active=active
        )

    def test_update_coupon_authenticated(self):
        """Test that authenticated users can update a coupon."""
        coupon = self.create_coupon(code="DISCOUNT10", discount_type='percentage', discount_value=10)

        update_data = {
            "discount_value": 15
        }
        response = self.client.patch(f"{self.url}{coupon.id}/", update_data)

        assert response.status_code == status.HTTP_200_OK
        coupon.refresh_from_db()
        assert coupon.discount_value == 15.00

    def test_update_coupon_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot update a coupon."""
        coupon = self.create_coupon(code="DISCOUNT10", discount_type='percentage', discount_value=10)

        update_data = {
            "discount_value": 15
        }
        unauthenticated_client = api_client()
        response = unauthenticated_client.patch(f"{self.url}{coupon.id}/", update_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN or status.HTTP_401_UNAUTHORIZED

    def test_delete_coupon_authenticated(self):
        """Test that authenticated users can delete a coupon."""
        coupon = self.create_coupon(code="DISCOUNT10", discount_type='percentage', discount_value=10)

        response = self.client.delete(f"{self.url}{coupon.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Coupon.objects.filter(id=coupon.id).count() == 0

    def test_delete_coupon_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot delete a coupon."""
        coupon = self.create_coupon(code="DISCOUNT10", discount_type='percentage', discount_value=10)

        unauthenticated_client = api_client()
        response = unauthenticated_client.delete(f"{self.url}{coupon.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN or status.HTTP_401_UNAUTHORIZED

    def test_update_coupon_not_found(self):
        """Test updating a non-existent coupon returns a 404 error."""
        update_data = {
            "discount_value": 15
        }
        response = self.client.patch(f"{self.url}9999/", update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_coupon_not_found(self):
        """Test deleting a non-existent coupon returns a 404 error."""
        response = self.client.delete(f"{self.url}9999/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
