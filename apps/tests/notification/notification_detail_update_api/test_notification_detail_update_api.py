import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestNotificationViews:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, notification_factory):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.notification = notification_factory(user=self.user, message="Test notification")
        self.url_detail = f'/api/notifications/{self.notification.id}/'
        self.url_update = f'/api/notifications/{self.notification.id}/'

    def test_get_notification_detail_view_authenticated(self):
        """Test that authenticated user can get the notification detail."""
        response = self.client.get(self.url_detail)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == "Test notification"

    def test_get_notification_detail_view_unauthorized(self, api_client):
        """Test that unauthorized user cannot get the notification detail."""
        client = api_client()
        response = client.get(self.url_detail)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_notification_view_authenticated(self):
        """Test that authenticated user can update notification status (is_read)."""
        data = {'is_read': True}
        response = self.client.patch(self.url_update, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] == True

        self.notification.refresh_from_db()
        assert self.notification.is_read is True

    def test_update_notification_view_unauthorized(self, api_client):
        """Test that unauthorized user cannot update the notification."""
        client = api_client()
        data = {'is_read': True}
        response = client.patch(self.url_update, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_notification_not_owned_by_user(self, user_factory, tokens, api_client):
        """Test that a user cannot update a notification not owned by them."""
        another_user = user_factory()
        data = {'is_read': True}

        access, _ = tokens(another_user)
        client = api_client(token=access)

        response = client.patch(self.url_update, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
