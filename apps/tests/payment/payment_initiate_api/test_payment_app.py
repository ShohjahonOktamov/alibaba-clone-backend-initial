import pytest
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
