import pytest
from rest_framework import status
from core import settings


@pytest.mark.order(1)
def test_product_app_created():
    assert "product" in settings.INSTALLED_APPS, "product app not installed"


@pytest.mark.order(2)
def test_product_app_exists():
    app_name = 'product'

    try:
        import product  # noqa
    except ImportError:
        assert False, f"{app_name} app folder missing"
    assert app_name in settings.INSTALLED_APPS, f"{app_name} app not installed"


@pytest.mark.order(3)
def test_product_model_created():
    """
    The function tests that the articles model is created.
    """
    try:
        from product.models import Category  # noqa
    except ImportError:
        assert False, f"Category model missing"


@pytest.mark.django_db
class TestCategoryViewSet:

    @pytest.fixture(autouse=True)
    def setup(self, user_factory, tokens, api_client):
        from user.models import Group

        self.api = '/api/products/categories/'

        self.user = user_factory()
        buyer_group = Group.objects.get(name="buyer")
        self.user.groups.add(buyer_group)
        self.user.save()

        self.access, _ = tokens(self.user)
        self.client = api_client(token=self.access)

        self.buyer_user = user_factory()
        self.buyer_access, _ = tokens(self.buyer_user)
        self.buyer_client = api_client(token=self.buyer_access)

        self.seller_user = user_factory()
        seller_group = Group.objects.get(name="seller")
        self.seller_user.groups.add(seller_group)
        self.seller_user.save()

        self.seller_access, _ = tokens(self.seller_user)
        self.seller_client = api_client(token=self.seller_access)

    @pytest.mark.parametrize(
        'client, expected_status, expected_count',
        [
            ('client', status.HTTP_200_OK, 5),
            ('seller_client', status.HTTP_200_OK, 5)
        ]
    )
    def test_list_categories(self, category_factory, client, expected_status, expected_count):
        category_factory.create_batch(expected_count)

        response = getattr(self, client).get(self.api)
        assert response.status_code == expected_status
        assert len(response.data['results']) == expected_count
        assert all('id' in category and 'name' in category for category in response.data['results'])

    @pytest.mark.parametrize(
        'search_query, expected_count',
        [
            ('Electronics', 1),
            ('Books', 1),
            ('Nonexistent', 0)
        ]
    )
    def test_list_categories_with_search(self, category_factory, search_query, expected_count):
        category_factory.create(name="Electronics")
        category_factory.create(name="Books")

        response = self.client.get(self.api, {'search': search_query})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == expected_count
        if expected_count > 0:
            assert response.data['results'][0]['name'] == search_query

    def test_retrieve_single_category(self, category_factory):
        category = category_factory.create()

        response = self.client.get(f'{self.api}{category.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(category.id)

    @pytest.mark.parametrize(
        'category_id, expected_status',
        [
            ('999999', status.HTTP_404_NOT_FOUND),
            ('incorrect-id', status.HTTP_404_NOT_FOUND)
        ]
    )
    def test_retrieve_invalid_category(self, category_id, expected_status):
        response = self.client.get(f'{self.api}{category_id}/')
        assert response.status_code == expected_status

    def test_unauthorized_access(self, api_client):
        client = api_client()
        response = client.get(self.api)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_category_products(self, category_factory, product_factory):
        category = category_factory.create()
        product_factory.create_batch(3, category=category)

        response = self.client.get(f'{self.api}{category.id}/products/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_no_permissions(self, category_factory):
        category = category_factory.create(name="Electronics")

        response = self.buyer_client.get(f'{self.api}{category.id}/products/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_seller_access(self, category_factory):
        category_factory.create(name="Electronics")

        response = self.seller_client.get(self.api)
        assert response.status_code == status.HTTP_200_OK
