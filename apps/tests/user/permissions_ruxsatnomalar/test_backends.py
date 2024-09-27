import pytest
from core import settings


@pytest.mark.order(1)
@pytest.mark.django_db
def test_user_exists():
    try:
        import user
    except ImportError:
        assert False, f"User app is missing"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_backends_exists():
    try:
        from user.backends import CustomModelBackend
    except ImportError:
        assert False, f"CustomModelBackend class is missing"


@pytest.mark.order(3)
def test_settings_authentication_exists():
    assert 'user.backends.CustomModelBackend' == settings.AUTHENTICATION_BACKENDS[
        0], "AUTHENTICATION_BACKENDS not in settings"
