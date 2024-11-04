from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from redis import Redis
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_400_BAD_REQUEST, HTTP_200_OK
from share.utils import generate_otp, redis_conn, check_otp, send_email

from apps.share.exceptions import OTPException
from .serializers import UserSerializer, VerifyCodeSerializer
from .services import UserService

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractBaseUser
    from rest_framework.permissions import BasePermission
    from rest_framework.request import Request

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


# Create your views here.

class SignUpView(GenericAPIView):
    serializer_class: "Type[UserSerializer]" = UserSerializer
    permission_classes: "tuple[type[BasePermission]]" = AllowAny,

    def post(self, request: "Request", *args, **kwargs) -> Response:
        serializer: UserSerializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        email: str = serializer.validated_data.get("email")
        if UserModel.objects.filter(email=email, is_verified=True).exists():
            return Response(data={
                "detail": _("User with this email already exists!")},
                status=HTTP_409_CONFLICT
            )

        phone_number: str = serializer.validated_data.get("phone_number")
        if UserModel.objects.filter(phone_number=phone_number, is_verified=True).exists():
            return Response(data={
                "detail": _("User with this phone number already exists!")},
                status=HTTP_409_CONFLICT
            )

        try:
            otp_code, otp_secret = generate_otp(phone_number_or_email=phone_number, check_if_exists=True)
            send_email(email=email, otp_code=otp_code)
            # print(otp_code)
        except OTPException:
            otp_secret: str = redis_conn.get(f"{phone_number}:otp_secret").decode()

        return Response(data={
            "phone_number": phone_number,
            "otp_secret": otp_secret},
            status=HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    serializer_class: "Type[VerifyCodeSerializer]" = VerifyCodeSerializer
    permission_classes: "tuple[type[BasePermission]]" = AllowAny,

    def patch(self, request: "Request", *args, **kwargs) -> Response:
        serializer: VerifyCodeSerializer = self.get_serializer(
            data=request.data, context={"otp_secret": kwargs.get("otp_secret")})

        serializer.is_valid(raise_exception=True)

        data: dict[str, str] = serializer.validated_data

        phone_number: str = data["phone_number"]
        otp_code: str = data["otp_code"]
        otp_secret: str = redis_conn.get(f"{phone_number}:otp_secret").decode()

        try:
            check_otp(phone_number_or_email=phone_number, otp_code=otp_code, otp_secret=otp_secret)
        except OTPException:
            return Response(
                data={"message": "Incorrect otp_code."},
                status=HTTP_400_BAD_REQUEST)

        redis_conn.delete(f"{phone_number}:otp")
        redis_conn.delete(f"{phone_number}:otp_secret")

        user: UserModel = UserModel.objects.filter(phone_number=phone_number).first()

        user.is_verified = True
        user.is_active = True
        user.save()

        tokens: dict[str, str] = UserService.create_tokens(user=user)

        return Response(
            data=tokens,
            status=HTTP_200_OK
        )
