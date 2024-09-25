import pytest
from rest_framework import status
from user.models import Group


@pytest.mark.django_db
class TestNotificationListView:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, tokens, user_factory, notification_factory):
        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.url_notifications = '/api/notifications/'

        self.notification1 = notification_factory(user=self.user, message="Test notification 1")
        self.notification2 = notification_factory(user=self.user, message="Test notification 2", is_read=True)

    def test_get_notifications_view_authenticated(self):
        response = self.client.get(self.url_notifications)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        assert any(notification['message'] == 'Test notification 1' for notification in response.data['results'])
        assert any(notification['message'] == 'Test notification 2' for notification in response.data['results'])

    @pytest.mark.parametrize("endpoint, expected_status", [
        ('/api/notifications/', status.HTTP_401_UNAUTHORIZED),
    ])
    def test_unauthenticated_access(self, api_client, endpoint, expected_status):
        client = api_client()
        response = client.get(endpoint)
        assert response.status_code == expected_status

    @pytest.mark.parametrize("is_read, expected_is_read", [
        (False, False),
        (True, True),
    ])
    def test_notification_read_status(self, is_read, expected_is_read):
        self.notification1.is_read = is_read
        self.notification1.save()

        response = self.client.get(self.url_notifications)
        assert response.status_code == status.HTTP_200_OK

        notification = next((n for n in response.data['results'] if n['id'] == str(self.notification1.id)), None)
        assert notification is not None, "Notification should exist in the response"
        assert notification['is_read'] == expected_is_read
