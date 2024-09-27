import pytest
from rest_framework import status
from core import settings
import uuid


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


@pytest.mark.order(4)
@pytest.mark.django_db
class TestWishlistListCreateView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens, product_factory):
        """Setup necessary data for each test."""
        from user.models import Group

        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.another_user = user_factory()

        self.another_access, _ = tokens(self.another_user)
        self.another_client = api_client(token=self.another_access)

        self.product = product_factory()

        self.url = '/api/wishlist/'

    def test_list_wishlist_authenticated(self, wishlist_factory):
        """Test that an authenticated user can retrieve their wishlist."""
        wishlist_factory(created_by=self.user, product=self.product)

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['product']['title'] == self.product.title

    def test_list_wishlist_unauthenticated(self):
        """Test that an unauthenticated user cannot retrieve a wishlist."""
        response = self.another_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_product_to_wishlist_success(self):
        """Test that a product can be added to the wishlist successfully."""
        from wishlist.models import Wishlist

        data = {
            'product_id': str(self.product.id)
        }
        response = self.client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        print("response ", response.data)
        assert Wishlist.objects.filter(created_by=self.user).count() == 1
        assert response.data['product']['id'] == self.product.id

    def test_add_existing_product_to_wishlist(self, wishlist_factory):
        """Test that adding a product already in the wishlist returns an error."""
        wishlist_factory(created_by=self.user, product=self.product)

        data = {
            'product_id': str(self.product.id)
        }

        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == 'Product is already in the wishlist.'

    def test_add_nonexistent_product_to_wishlist(self):
        """Test that adding a non-existent product to the wishlist returns a 404 error."""
        data = {
            'product_id': str(uuid.uuid4())
        }

        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['product_id'][0] == 'Product not found.'
