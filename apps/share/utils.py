from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from user.models import Group
from user.models import Policy

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


def add_permissions(obj: UserModel | Group | Policy, permissions: list[str]) -> None:
    def get_permission(permission: str) -> list[Permission]:
        app_label, codename = permission.split('.')
        try:
            model: str = codename.split('_')[1]
            content_type, created = ContentType.objects.get_or_create(app_label=app_label, model=model)
            permission, created = Permission.objects.get_or_create(codename=codename, content_type=content_type)
        except (IndexError, ContentType.DoesNotExist):
            permission, created = Permission.objects.get_or_create(
                codename=codename
            )
        return permission

    if isinstance(obj, UserModel):
        obj.user_permissions.clear()
        obj.user_permissions.add(*map(get_permission, permissions))
    elif isinstance(obj, (Group, Policy)):
        obj.permissions.clear()
        obj.permissions.add(*map(get_permission, permissions))
