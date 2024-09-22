import pytest
from core import settings


@pytest.mark.order(1)
def test_stripe_exists():
    try:
        import stripe
    except ImportError:
        assert False, "Stripe is not installed."


@pytest.mark.order(2)
def test_stripe_keys_exist_in_settings():
    assert hasattr(settings, 'STRIPE_TEST_PUBLIC_KEY'), "STRIPE_TEST_PUBLIC_KEY is missing in settings."
    assert settings.STRIPE_TEST_PUBLIC_KEY, "STRIPE_TEST_PUBLIC_KEY is set but empty."
    assert hasattr(settings, 'STRIPE_TEST_SECRET_KEY'), "STRIPE_TEST_SECRET_KEY is missing in settings."
    assert settings.STRIPE_TEST_SECRET_KEY, "STRIPE_TEST_SECRET_KEY is set but empty."


@pytest.mark.order(3)
def test_stripe_keys_format():
    assert settings.STRIPE_TEST_PUBLIC_KEY.startswith('pk_test_'), "STRIPE_TEST_PUBLIC_KEY format is invalid."
    assert settings.STRIPE_TEST_SECRET_KEY.startswith('sk_test_'), "STRIPE_TEST_SECRET_KEY format is invalid."
