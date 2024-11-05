from typing import TYPE_CHECKING, Type, Any, Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from redis import Redis
from rest_framework.generics import GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_403_FORBIDDEN
from share.permissions import GeneratePermissions
from share.utils import generate_otp, redis_conn, check_otp

from apps.share.exceptions import OTPException
from .models import BuyerUser, SellerUser
from .serializers import UserSerializer, VerifyCodeSerializer, LoginSerializer, UsersMeSerializer, BuyerUserSerializer, \
    SellerUserSerializer
from .services import UserService
from .tasks import send_email

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from rest_framework.permissions import BasePermission
    from rest_framework.request import Request
    from django.db.models import QuerySet

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


# Create your views here.

class SignUpView(GenericAPIView):
    serializer_class: Type[UserSerializer] = UserSerializer
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
            send_email.delay(email=email, otp_code=otp_code)
            # print(otp_code)
        except OTPException:
            otp_secret: str = redis_conn.get(f"{phone_number}:otp_secret").decode()

        return Response(data={
            "phone_number": phone_number,
            "otp_secret": otp_secret},
            status=HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    serializer_class: Type[VerifyCodeSerializer] = VerifyCodeSerializer
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


class LoginView(GenericAPIView):
    queryset: "QuerySet[UserModel]" = UserModel.objects.filter(is_verified=True, is_active=True)
    serializer_class: Type[LoginSerializer] = LoginSerializer
    permission_classes: "tuple[type[BasePermission]]" = AllowAny,

    def post(self, request: "Request", *args, **kwargs) -> Response:
        serializer: LoginSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data: dict[str, str] = serializer.validated_data

        user: UserModel = UserService.authenticate(
            email_or_phone_number=data["email_or_phone_number"],
            password=data["password"]
        )

        tokens: dict[str, str] = UserService.create_tokens(user=user)

        return Response(
            data=tokens,
            status=HTTP_200_OK
        )


class UserMeView(GeneratePermissions, RetrieveAPIView, UpdateAPIView):
    queryset: "QuerySet[UserModel]" = UserModel.objects.all()
    serializer_class: Type[UsersMeSerializer] = UsersMeSerializer
    permission_classes: "tuple[type[BasePermission]]" = IsAuthenticated,

    def get_object(self) -> UserModel:
        return self.request.user

    def get(self, request: "Request", *args, **kwargs) -> Response:
        user: UserModel = self.get_object()
        serializer: UsersMeSerializer = UsersMeSerializer(instance=self.get_object())
        if serializer.get_trader_user(instance=user) is None:
            return Response(status=HTTP_403_FORBIDDEN)

        return Response(data=serializer.data)

    def patch(self, request: "Request", *args, **kwargs) -> Response:
        user: UserModel = self.get_object()
        serializer: UsersMeSerializer = UsersMeSerializer(instance=self.get_object())
        user_trade_role: Literal["buyer", "seller"] | None = serializer.get_user_trade_role(instance=user)
        if user_trade_role is None:
            return Response(status=HTTP_403_FORBIDDEN)

        serializer: UsersMeSerializer = self.serializer_class(
            instance=user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if user_trade_role == "buyer":
            trader_user_type: Type[BuyerUser] = BuyerUser
            serializer_type: Type[BuyerUserSerializer] = BuyerUserSerializer
        else:
            trader_user_type: Type[SellerUser] = SellerUser
            serializer_type: Type[SellerUserSerializer] = SellerUserSerializer

        trader_user: BuyerUser | SellerUser = trader_user_type.objects.filter(user=user).first()
        if trader_user is not None:
            data: dict[str, Any | None] = {
                field: request.data[field] for field in serializer_type.Meta.fields if field in request.data
            }
            serializer: BuyerUserSerializer | SellerUserSerializer = serializer_type(
                instance=trader_user,
                data=data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(data=UsersMeSerializer(instance=self.get_object()).data)
