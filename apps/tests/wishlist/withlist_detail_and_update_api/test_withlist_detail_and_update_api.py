import pytest
from rest_framework import status
from wishlist.models import Wishlist
from user.models import Group
import uuid


@pytest.mark.django_db
class TestWishlistRetrieveDeleteView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens, product_factory, wishlist_factory):
        """Setup necessary data for each test."""
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
        self.wishlist_item = wishlist_factory(created_by=self.user, product=self.product)

        self.url = f'/api/wishlist/{self.wishlist_item.id}/'

    def test_retrieve_wishlist_item_success(self):
        """Test that an authenticated user can retrieve a specific wishlist item."""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['product']['id'] == str(self.product.id)
        assert response.data['product']['title'] == self.product.title

    def test_retrieve_wishlist_item_no_perm(self):
        """Test that an no prem user cannot retrieve a wishlist item."""
        response = self.another_client.get(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_nonexistent_wishlist_item(self):
        """Test that retrieving a non-existent wishlist item returns a 404 error."""
        nonexistent_url = f'/api/wishlist/{uuid.uuid4()}/'
        response = self.client.get(nonexistent_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_wishlist_item_success(self):
        """Test that an authenticated user can successfully delete a wishlist item."""
        response = self.client.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Wishlist.objects.filter(created_by=self.user, product=self.product).exists()

    def test_delete_wishlist_item_no_perm(self):
        """Test that an no prem user cannot delete a wishlist item."""
        response = self.another_client.delete(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_nonexistent_wishlist_item(self):
        """Test that trying to delete a non-existent wishlist item returns a 404 error."""
        nonexistent_url = f'/api/wishlist/{uuid.uuid4()}/'
        response = self.client.delete(nonexistent_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
