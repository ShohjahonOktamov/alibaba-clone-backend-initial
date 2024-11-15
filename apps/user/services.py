from typing import TYPE_CHECKING, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from share.services import TokenService

from .enums import TokenType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


class UserService():
    @classmethod
    def authenticate(cls, email_or_phone_number: str, password: str,
                     quiet: bool = False) -> ValidationError | UserModel | None:
        try:
            user: UserModel = UserModel.objects.filter(is_verified=True, is_active=True).get(
                Q(email=email_or_phone_number) | Q(phone_number=email_or_phone_number)
            )
        except UserModel.DoesNotExist:
            if quiet:
                return
            else:
                raise ValidationError(detail="Invalid user credentials.", code="invalid_user_credentials")

        if not check_password(password=password, encoded=user.password):
            if quiet:
                return
            else:
                raise ValidationError(detail="Invalid user credentials.", code="invalid_user_credentials")

        return user

    @classmethod
    def create_tokens(cls, user: UserModel, access: str | bytes | None = None, refresh: str | bytes | None = None) -> \
    dict[str, str]:
        if None in (access, refresh):
            refresh: RefreshToken = RefreshToken.for_user(user)
            access: str = str(getattr(refresh, "access_token"))
            refresh: str = str(refresh)

        TokenService.add_token_to_redis(
            user_id=user.id,
            token=access,
            token_type=TokenType.ACCESS,
            lifetime=settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME"),
        )

        TokenService.add_token_to_redis(
            user_id=user.id,
            token=refresh,
            token_type=TokenType.REFRESH,
            lifetime=settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME"),
        )

        return {"access": access, "refresh": refresh}
