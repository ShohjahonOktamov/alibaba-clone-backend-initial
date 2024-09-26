import factory
from faker import Faker

fake = Faker()


class WishlistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'wishlist.Wishlist'

    id = factory.Faker('uuid4')
    created_by = factory.SubFactory('tests.factories.user_factory.UserFactory')
    product = factory.SubFactory('tests.factories.product_factory.ProductFactory')
    created_at = factory.Faker('date_time_this_decade', tzinfo=None)
    updated_at = factory.Faker('date_time_this_decade', tzinfo=None)
