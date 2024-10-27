from typing import TYPE_CHECKING

import yaml
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from share.enums import UserRole, PolicyNameEnum
from share.utils import add_permissions
from user.models import Policy, Group

from core.settings import config

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


class Command(BaseCommand):
    help: str = "Create initial data, including user groups and policies"

    def handle(self, *args, **options) -> None:
        self.create_superuser()
        self.create_default_policies()
        for group_name in (UserRole.BUYER.value, UserRole.SELLER.value, UserRole.ADMIN.value):
            group_object, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(msg=self.style.SUCCESS(f"{group_name} group created successfully"))
            policy_name: str = f"{group_name}_policy"
            if policy_name not in PolicyNameEnum.values():
                self.stdout.write(msg=self.style.ERROR(
                    f"{policy_name} not exists in available policy names. Add new policy name to PolicyNameEnum")
                )
                return
            policy: Policy = Policy.objects.get(name=f"{group_name}_policy", is_active=True)
            group_object.policies.add(policy)
        self.stdout.write(msg=self.style.SUCCESS("Initial data creation complete"))

    def create_superuser(self) -> None:
        superuser_email: str = config("DJANGO_SUPERUSER_EMAIL", cast=str)
        superuser_password: str = config("DJANGO_SUPERUSER_PASSWORD", cast=str)
        if not UserModel.objects.filter(email=superuser_email).exists():
            UserModel.objects.create_superuser(email=superuser_email,
                                               password=superuser_password)
            self.stdout.write(self.style.SUCCESS("Superuser created successfully"))

    def create_default_policies(self) -> None:
        with open(".fixtures/policies.yaml", 'r', encoding="utf-8") as file:
            policies_data: dict[str, list[str]] | None = yaml.safe_load(stream=file)
            if policies_data is not None:
                for policy_name, permissions in policies_data.items():
                    if policy_name not in PolicyNameEnum.values():
                        self.stdout.write(msg=self.style.ERROR(
                            f"{policy_name} does not exist in available policy names. \
                            Add new policy name to PolicyNameEnum")
                        )
                        return
                    policy, created = Policy.objects.get_or_create(name=policy_name, is_active=True)
                    self.stdout.write(msg=self.style.SUCCESS(
                        f"{policy_name} policy created successfully with {len(permissions)} permissions")
                    )
                    add_permissions(policy, permissions)
