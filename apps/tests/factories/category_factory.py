import factory

from product.models import Category
from faker import Faker

fake = Faker()


class CategoryFactory(factory.django.DjangoModelFactory):
    """This class will create fake data for category"""

    class Meta:
        model = Category

    id = factory.Faker('uuid4')
    name = factory.LazyAttribute(lambda o: fake.word())
    is_active = True
    created_at = factory.Faker('date_time_this_decade', tzinfo=None)
