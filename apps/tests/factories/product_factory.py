import factory

from product.models import Product
from faker import Faker

fake = Faker()


class ProductFactory(factory.django.DjangoModelFactory):
    """This class will create fake data for category"""

    class Meta:
        model = Product

    id = factory.Faker('uuid4')
    seller = factory.SubFactory('tests.factories.user_factory.UserFactory')
    category = factory.SubFactory('tests.factories.category_factory.CategoryFactory')
    title = factory.LazyAttribute(lambda o: fake.word())
    description = factory.LazyAttribute(lambda o: fake.word())
    price = factory.Faker('pyfloat', left_digits=2, right_digits=2, positive=True)
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
    created_at = factory.Faker('date_time_this_decade', tzinfo=None)
