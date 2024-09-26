import pytest
from core import settings


@pytest.mark.order(1)
def test_notification_app_exists():
    try:
        import notification
    except ImportError:
        assert False, "Notification app is not installed."


@pytest.mark.order(2)
def test_notification_app_created():
    assert "notification" in settings.INSTALLED_APPS, "notification app not installed"


@pytest.mark.order(3)
def test_notification_model_created():
    try:
        from notification.models import Notification
    except ImportError:
        assert False, "Notification model is not created."
