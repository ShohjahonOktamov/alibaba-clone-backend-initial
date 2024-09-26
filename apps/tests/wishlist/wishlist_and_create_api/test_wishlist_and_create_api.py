import pytest
from rest_framework import status
from wishlist.models import Wishlist
from user.models import Group
import uuid


@pytest.mark.django_db
class TestWishlistListCreateView:

    @pytest.fixture(autouse=True)
    def setup(self, api_client, user_factory, tokens, product_factory):
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
