import datetime
from typing import TYPE_CHECKING, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from redis import Redis
from user.enums import TokenType
from uuid import UUID
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
            user_id: UUID,
            token: str,
            token_type: TokenType,
            lifetime: datetime.timedelta,
    ) -> None:
        redis_client: Redis = cls.get_redis_client()

        token_key: str = f"user:{user_id}:{token_type}"

        valid_tokens: set[str] | None = cls.get_valid_tokens(user_id, token_type)
        if valid_tokens is not None:
            cls.delete_tokens(user_id=user_id, token_type=token_type)
        redis_client.sadd(token_key, token)
        redis_client.expire(name=token_key, time=lifetime)

    @classmethod
    def delete_tokens(cls, user_id: int, token_type: TokenType) -> None:
        redis_client: Redis = cls.get_redis_client()
        token_key: str = f"user:{user_id}:{token_type}"
        valid_tokens: set[str] | None = redis_client.smembers(token_key)
        if valid_tokens is not None:
            redis_client.delete(token_key)
