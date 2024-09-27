import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker()

model_name = 'User'
app_name = 'user'

app_name_2 = 'share'


@pytest.mark.order(1)
@pytest.mark.django_db
def test_users_app_exists():
    try:
        import user
    except ImportError:
        assert False, f"{app_name} app folder missing"
    assert app_name in settings.INSTALLED_APPS, f"{app_name} app not installed"


@pytest.mark.order(2)
@pytest.mark.django_db
def test_share_app_exists():
    try:
        import share
    except ImportError:
        assert False, f"{app_name_2} app folder missing"
    assert app_name in settings.INSTALLED_APPS, f"{app_name_2} app not installed"


@pytest.mark.order(3)
@pytest.mark.django_db
def test_custom_user_model():
    assert settings.AUTH_USER_MODEL == f"{app_name}.{model_name}", f"{model_name} model not set"
    User = get_user_model()  # noqa
    assert User is not None, f"{model_name} model not found"

    assert User._meta.db_table == "user", f"{model_name} model db_table not set"
    assert User._meta.ordering == ["-created_at"], f"{model_name} model ordering not set"

    user = User.objects.create(
        email='testuser@gmail.com',
        phone_number='+998930000000',
        first_name='Abdulaziz',
        last_name='Komilov',
        gender='male'
    )

    assert user is not None, f"{model_name} model not created"
    user.set_password('abdulazizK123')
    user.save()
    assert user.check_password('abdulazizK123'), f"{model_name} model password not set"
    assert user.first_name == 'Abdulaziz', f"{model_name} model first_name not set"
    assert user.last_name == 'Komilov', f"{model_name} model last_name not set"
    assert user.email == 'testuser@gmail.com', f"{model_name} model email not set"
    assert user.phone_number == '+998930000000', f"{model_name} model phone_number not set"
    assert user.groups.count() == 0, f"{model_name} model groups not set"
    assert user.policies.count() == 0, f"{model_name} model policies not set"


@pytest.mark.order(4)
@pytest.mark.django_db
def test_group_model_created():
    """
    The function tests that the Group model is created.
    """
    try:
        from user.models import Group
    except ImportError:
        assert False, "Group model not created"

    assert Group._meta.db_table == "group", "Group model not created"
    assert Group._meta.ordering == ["-created_at"], "Group model not created"

    group = Group.objects.create(name="TestGroup")

    assert group is not None, "Group model not created"
    assert group.name == "TestGroup", "Group model not created"
    assert group.policies.count() == 0, "Group model not created"
    assert group.permissions.count() == 0, "Group model not created"


@pytest.mark.order(5)
@pytest.mark.django_db
def test_policy_model_created():
    """
    The function tests that the Policy model is created.
    """
    try:
        from user.models import Policy
    except ImportError:
        assert False, "Policy model not created"

    assert Policy._meta.db_table == "policy", "Policy model not created"
    assert Policy._meta.ordering == ["-created_at"], "Policy model not created"

    policy = Policy.objects.create(name="TestPolicy")

    assert policy is not None, "Policy model not created"
    assert policy.name == "TestPolicy", "Policy model not created"
    assert policy.permissions.count() == 0, "Policy model not created"


@pytest.mark.order(6)
@pytest.mark.django_db
def test_seller_user_model_created():
    """
    The function tests that the SellerUser model is created.
    """
    try:
        from user.models import SellerUser
    except ImportError:
        assert False, "SellerUser model not created"

    User = get_user_model()
    import datetime as dt

    seller_user = SellerUser.objects.create(
        company="Mohirpool",
        user=User.objects.create(
            email='testuser@gmail.com',
            phone_number='+998930000000',
            first_name='Abdulaziz',
            last_name='Komilov',
            gender='male'
        ),
        bio="Test bio",
        birth_date=dt.date(2000, 1, 1),
        country="Uzbekistan",
        city="Tashkent",
        district="Toshkent",
        street_address="Toshkent",
        postal_code="100000",
        second_phone_number="+998930000000",
        building_number=1,
        apartment_number=1
    )

    assert seller_user is not None, "SellerUser model not created"
    assert seller_user.company == 'Mohirpool', "SellerUser model not created"
    assert seller_user.user.email == 'testuser@gmail.com', "SellerUser model not created"
    assert seller_user.user.phone_number == '+998930000000', "SellerUser model not created"
    assert seller_user.bio == 'Test bio', "SellerUser model not created"
    assert seller_user.birth_date == dt.date(2000, 1, 1), "SellerUser model not created"
    assert seller_user.country == 'Uzbekistan', "SellerUser model not created"
    assert seller_user.city == 'Tashkent', "SellerUser model not created"
    assert seller_user.district == 'Toshkent', "SellerUser model not created"
    assert seller_user.street_address == 'Toshkent', "SellerUser model not created"
    assert seller_user.postal_code == '100000', "SellerUser model not created"
    assert seller_user.second_phone_number == '+998930000000', "SellerUser model not created"
    assert seller_user.building_number == 1, "SellerUser model not created"
    assert seller_user.apartment_number == 1, "SellerUser model not created"


@pytest.mark.order(7)
@pytest.mark.django_db
def test_buyer_user_model_created():
    """
    The function tests that the SellerUser model is created.
    """
    try:
        from user.models import BuyerUser
    except ImportError:
        assert False, "BuyerUser model not created"

    User = get_user_model()
    import datetime as dt

    buyer_user = BuyerUser.objects.create(
        user=User.objects.create(
            email='testuser@gmail.com',
            phone_number='+998930000000',
            first_name='Abdulaziz',
            last_name='Komilov',
            gender='male'
        ),
        bio="Test bio",
        birth_date=dt.date(2000, 1, 1),
        country="Uzbekistan",
        city="Tashkent",
        district="Toshkent",
        street_address="Toshkent",
        postal_code="100000",
        second_phone_number="+998930000000",
        building_number=1,
        apartment_number=1
    )

    assert buyer_user is not None, "BuyerUser model not created"
    assert buyer_user.user.email == 'testuser@gmail.com', "BuyerUser model not created"
    assert buyer_user.user.phone_number == '+998930000000', "BuyerUser model not created"
    assert buyer_user.bio == 'Test bio', "BuyerUser model not created"
    assert buyer_user.birth_date == dt.date(2000, 1, 1), "BuyerUser model not created"
    assert buyer_user.country == 'Uzbekistan', "BuyerUser model not created"
    assert buyer_user.city == 'Tashkent', "BuyerUser model not created"
    assert buyer_user.district == 'Toshkent', "BuyerUser model not created"
    assert buyer_user.street_address == 'Toshkent', "BuyerUser model not created"
    assert buyer_user.postal_code == '100000', "BuyerUser model not created"
    assert buyer_user.second_phone_number == '+998930000000', "BuyerUser model not created"
    assert buyer_user.building_number == 1, "BuyerUser model not created"
    assert buyer_user.apartment_number == 1, "BuyerUser model not created"
