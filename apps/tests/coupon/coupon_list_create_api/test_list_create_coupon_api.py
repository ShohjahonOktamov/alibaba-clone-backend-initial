import pytest
from rest_framework import status
from django.utils import timezone
from core import settings
from datetime import timedelta


@pytest.mark.order(1)
def test_coupon_app_exists():
    try:
        import coupon
    except ImportError:
        assert False, "Coupon app is not installed."


@pytest.mark.order(2)
def test_coupon_app_created():
    assert "coupon" in settings.INSTALLED_APPS, "coupon app not installed"


@pytest.mark.order(3)
def test_coupon_model_created():
    try:
        from coupon.models import Coupon
    except ImportError:
        assert False, "Coupon model is not created."


@pytest.mark.order(4)
@pytest.mark.django_db
class TestCouponListCreateView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens):
        """Setup common variables for each test."""
        from user.models import Group

        self.user = user_factory()
        seller_group = Group.objects.get(name="seller")
        self.user.groups.add(seller_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.url = '/api/coupons/'

    def create_coupon(self, code="DISCOUNT10", discount_type='percentage', discount_value=10, active=True):
        """Helper method to create a coupon."""
        from coupon.models import Coupon

        return Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30),
            active=active
        )

    def test_get_coupon_list_view_authenticated(self):
        """Test that authenticated users can list coupons."""
        self.create_coupon(code="DISCOUNT10", discount_type='percentage', discount_value=10)
        self.create_coupon(code="SAVE20", discount_type='fixed', discount_value=20)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        for coupon in response.data['results']:
            assert 'code' in coupon
            assert 'discount_type' in coupon
            assert 'discount_value' in coupon
            assert coupon['active'] is True

    def test_create_coupon_authenticated(self):
        """Test that authenticated users can create a coupon."""
        data = {
            "code": "NEWCOUPON50",
            "discount_type": "fixed",
            "discount_value": 50.00,
            "active": True,
            "valid_from": timezone.now().isoformat(),
            "valid_until": (timezone.now() + timedelta(days=30)).isoformat()
        }

        response = self.client.post(self.url, data)
        print("response ", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['code'] == data['code']
        assert response.data['discount_type'] == data['discount_type']
        assert response.data['active'] == data['active']

    def test_get_coupon_list_view_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list coupons."""
        unauthenticated_client = api_client()
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN or status.HTTP_401_UNAUTHORIZED

    def test_create_coupon_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot create a coupon."""
        data = {
            "code": "UNAUTHCOUPON",
            "discount_type": "percentage",
            "discount_value": 30.00,
            "active": True,
            "valid_from": timezone.now().isoformat(),
            "valid_until": (timezone.now() + timedelta(days=30)).isoformat()
        }
        unauthenticated_client = api_client()
        response = unauthenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN or status.HTTP_401_UNAUTHORIZED
