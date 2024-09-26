import pytest
from core import settings


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
