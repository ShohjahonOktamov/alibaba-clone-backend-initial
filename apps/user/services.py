import datetime
from typing import TYPE_CHECKING, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from redis import Redis
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .enums import TokenType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


class TokenService:
    @classmethod
    def get_redis_client(cls) -> Redis:
        return Redis.from_url(settings.REDIS_URL)

    @classmethod
    def get_valid_tokens(cls, user_id: int, token_type: TokenType) -> set[str] | None:
        redis_client: Redis = cls.get_redis_client()
        token_key: str = f"user:{user_id}:{token_type}"
        valid_tokens: set[str] | None = redis_client.smembers(token_key)
        return valid_tokens

    @classmethod
    def add_token_to_redis(
            cls,
            user_id: int,
            token: str,
            token_type: TokenType,
            expire_time: datetime.timedelta,
    ) -> None:
        redis_client: Redis = cls.get_redis_client()

        token_key: str = f"user:{user_id}:{token_type}"

        valid_tokens: set[str] | None = cls.get_valid_tokens(user_id, token_type)
        if valid_tokens is not None:
            cls.delete_tokens(user_id=user_id, token_type=token_type)
        redis_client.sadd(token_key, token)
        redis_client.expire(name=token_key, time=expire_time)

    @classmethod
    def delete_tokens(cls, user_id: int, token_type: TokenType) -> None:
        redis_client: Redis = cls.get_redis_client()
        token_key: str = f"user:{user_id}:{token_type}"
        valid_tokens: set[str] | None = redis_client.smembers(token_key)
        if valid_tokens is not None:
            redis_client.delete(token_key)


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
    def create_tokens(cls, user: UserModel, access: str = None, refresh: str = None) -> dict[str, str]:
        if None in (access, refresh):
            refresh: RefreshToken = RefreshToken.for_user(user)
            access: str = str(getattr(refresh, "access_token"))
            refresh: str = str(refresh)

        TokenService.add_token_to_redis(
            user_id=user.id,
            token=refresh,
            token_type=TokenType.REFRESH,
            expire_time=settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME"),
        )

        return {"access": access, "refresh": refresh}
