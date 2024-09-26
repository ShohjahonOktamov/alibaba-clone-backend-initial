import pytest
from core import settings


@pytest.mark.order(1)
def test_wishlist_app_exists():
    try:
        import wishlist
    except ImportError:
        assert False, "Wishlist app is not installed."


@pytest.mark.order(2)
def test_wishlist_app_created():
    assert "wishlist" in settings.INSTALLED_APPS, "wishlist app not installed"


@pytest.mark.order(3)
def test_notification_model_created():
    try:
        from wishlist.models import Wishlist
    except ImportError:
        assert False, "Wishlist model is not created."
