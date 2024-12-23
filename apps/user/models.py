from uuid import uuid4

from django.contrib.auth.models import Permission, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models import Model, CharField, BooleanField, ManyToManyField, ForeignKey, DateTimeField, AutoField, \
    UUIDField, CASCADE, BinaryField, DateField, EmailField, OneToOneField


# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    objects: UserManager = UserManager()

    class Meta:
        db_table: str = "user"
        verbose_name: str = "User"
        verbose_name_plural: str = "Users"
        ordering: list[str] = ["-created_at"]

    id = UUIDField(primary_key=True, default=uuid4)
    gender = CharField(max_length=10)
    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    groups = ManyToManyField(blank=True, to="Group", related_name="custom_user_groups")
    phone_number = CharField(max_length=13, null=True)
    email = EmailField(max_length=255, blank=True, null=True)
    password = CharField(max_length=255)
    policies = ManyToManyField(blank=True, to="Policy")
    user_permissions = ManyToManyField(to=Permission, related_name="custom_user_permissions", blank=True)
    is_verified = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True, null=True)
    last_login = DateTimeField(auto_now=True, null=True)
    created_by = ForeignKey(to="User", null=True, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    USERNAME_FIELD: str = 'id'

    def __str__(self) -> str:
        return str(self.phone_number)


class Policy(Model):
    class Meta:
        db_table: str = "policy"
        verbose_name: str = "Policy"
        verbose_name_plural: str = "Policies"
        ordering: list[str] = ["-created_at"]

    policy_choices = [
        ("admin_policy", "ADMIN_POLICY"),
        ("seller_policy", "SELLER_POLICY"),
        ("buyer_policy", "BUYER_POLICY")
    ]

    id = UUIDField(primary_key=True, default=uuid4)
    name = CharField(max_length=13, unique=True, choices=policy_choices)
    permissions = ManyToManyField(to=Permission)
    is_active = BooleanField(default=False)
    created_by = ForeignKey(to=User, null=True, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class Group(Model):
    class Meta:
        db_table: str = "group"
        verbose_name: str = "Group"
        verbose_name_plural: str = "Groups"
        ordering: list[str] = ["-created_at"]

    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    policies = ManyToManyField(to=Policy)
    permissions = ManyToManyField(to=Permission, related_name="custom_group_permissions")
    is_active = BooleanField(default=False)
    created_by = ForeignKey(to=User, null=True, on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return str(self.name)


class SellerUser(Model):
    class Meta:
        db_table: str = "seller"
        verbose_name: str = "Seller users"
        verbose_name_plural: str = "Seller user"

    id = UUIDField(primary_key=True, default=uuid4)
    user = ForeignKey(to=User, on_delete=CASCADE)
    company = CharField(max_length=50, null=True)
    photo = BinaryField(null=True)
    bio = CharField(max_length=255, null=True)
    birth_date = DateField(null=True)
    country = CharField(max_length=50, null=True)
    city = CharField(max_length=50, null=True)
    district = CharField(max_length=50, null=True)
    street_address = CharField(max_length=50, null=True)
    postal_code = CharField(max_length=10, null=True)
    second_phone_number = CharField(max_length=13, null=True)
    building_number = CharField(max_length=50, null=True)
    apartment_number = CharField(max_length=50, null=True)
    created_by = OneToOneField(to=User, null=True, on_delete=CASCADE, related_name="seller")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)


class BuyerUser(Model):
    class Meta:
        db_table: str = "buyer"
        verbose_name: str = "Buyer user"
        verbose_name_plural: str = "Buyer users"
        ordering: list[str] = ["-created_at"]

    id: UUIDField = UUIDField(primary_key=True, default=uuid4)
    user: ForeignKey = ForeignKey(to=User, on_delete=CASCADE)
    photo: BinaryField = BinaryField(null=True)
    bio: CharField = CharField(max_length=255, null=True)
    birth_date = DateField(null=True)
    country = CharField(max_length=50, null=True)
    city = CharField(max_length=50, null=True)
    district = CharField(max_length=50, null=True)
    street_address = CharField(max_length=50, null=True)
    postal_code = CharField(max_length=10, null=True)
    second_phone_number = CharField(max_length=13, null=True)
    building_number = CharField(max_length=50, null=True)
    apartment_number = CharField(max_length=50, null=True)
    created_by = OneToOneField(to=User, null=True, on_delete=CASCADE, related_name="buyer")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
