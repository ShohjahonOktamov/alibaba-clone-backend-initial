from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthUser
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import Token
from share.services import TokenService

from .enums import TokenType

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractUser
    from rest_framework.request import Request

UserModel: "Type[AbstractUser]" = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: "Request") -> tuple[AuthUser, Token] | None:
        header: bytes | None = self.get_header(request=request)
        if header is None:
            return

        raw_token: bytes | None = self.get_raw_token(header=header)
        if raw_token is None:
            return

        user, access_token = super().authenticate(request=request)
        if not self.is_valid_access_token(user=user, access_token=access_token):
            raise AuthenticationFailed("Invalid Access Token")

        return user, access_token

    @classmethod
    def is_valid_access_token(cls, user: UserModel, access_token: Token) -> bool | None:
        valid_access_tokens: set[str] = TokenService.get_valid_tokens(user_id=user.id, token_type=TokenType.ACCESS)
        if valid_access_tokens and str(object=access_token).encode() not in valid_access_tokens:
            raise AuthenticationFailed(detail="Invalid User credentials")
        return True
