import factory

from faker import Faker
from notification.models import Notification

fake = Faker()


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    id = factory.Faker('uuid4')
    user = factory.SubFactory('tests.factories.user_factory.UserFactory')
    type = 'order'
    message = factory.LazyAttribute(lambda o: fake.word())
    is_read = False
