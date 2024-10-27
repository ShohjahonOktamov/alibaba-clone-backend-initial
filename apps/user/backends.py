from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

if TYPE_CHECKING:
    from typing import Type
    from django.http import HttpRequest
    from django.contrib.auth.models import AbstractUser, Permission
    from django.db.models import QuerySet, ManyToManyField

UserModel: "Type[AbstractUser]" = get_user_model()


class CustomModelBackend(ModelBackend):
    def authenticate(self, request: "HttpRequest", username: str | None = None, password: str | None = None,
                     **kwargs) -> UserModel | None:
        if not username:
            return

        try:
            if '@' in username:
                username_field: str = "email"
            else:
                username_field: str = "phone_number"

            users: "QuerySet[UserModel]" = UserModel.objects.filter(**{username_field: username})
            if users.exists():
                user: UserModel = users.first()
            else:
                return
        except UserModel.DoesNotExist:
            return

        if user.check_password(password) and self.user_can_authenticate(user=user):
            return user

    def user_can_authenticate(self, user: UserModel) -> bool:
        return user.is_active and user.is_verified

    def get_user(self, user_id: int) -> UserModel | None:
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return

    def _get_user_permissions(self, user_obj: UserModel) -> "QuerySet[Permission]":
        all_user_permissions: "QuerySet[Permission]" = UserModel.user_permissions.all()
        for policy in user_obj.policies.filter(is_active=True):
            all_user_permissions |= policy.permissions.all()
        return all_user_permissions

    def _get_group_permissions(self, user_obj: UserModel) -> "QuerySet[Permission]":
        user_groups_field: ManyToManyField = UserModel._meta.get_field("groups")
        user_groups_query: str = "custom_group__%s" % user_groups_field.related_query_name()
        all_group_permissions: QuerySet[Permission] = Permission.objects.filter(**{user_groups_query: user_obj})
        for group in user_obj.groups.filter(is_active=True):
            for policy in group.policies.filter(is_active=True):
                all_group_permissions |= policy.permissions.all()
        return all_group_permissions
