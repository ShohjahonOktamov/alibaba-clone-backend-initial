from secrets import token_urlsafe
from typing import TYPE_CHECKING, Type, Any, Literal

from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from redis import Redis
from rest_framework.generics import GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_400_BAD_REQUEST, HTTP_200_OK, \
    HTTP_403_FORBIDDEN
from share.permissions import GeneratePermissions
from share.utils import generate_otp, redis_conn, check_otp

from apps.share.exceptions import OTPException
from .models import BuyerUser, SellerUser
from .serializers import UserSerializer, VerifyCodeSerializer, LoginSerializer, UsersMeSerializer, BuyerUserSerializer, \
    SellerUserSerializer, ChangePasswordSerializer, ForgotPasswordSerializer, ForgotPasswordVerifySerializer, \
    ResetPasswordSerializer
from .services import UserService
from .tasks import send_email

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from rest_framework.request import Request
    from django.db.models import QuerySet

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


# Create your views here.

class SignUpView(GenericAPIView):
    serializer_class: Type[UserSerializer] = UserSerializer
    permission_classes: tuple[type[AllowAny]] = AllowAny,

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
            otp_code, otp_secret = generate_otp(phone_number_or_email=phone_number)
            send_email.delay(email=email, otp_code=otp_code)
        except OTPException:
            otp_secret: str = redis_conn.get(f"{phone_number}:otp_secret").decode()

        return Response(data={
            "phone_number": phone_number,
            "otp_secret": otp_secret},
            status=HTTP_201_CREATED)


class VerifyView(GenericAPIView):
    serializer_class: Type[VerifyCodeSerializer] = VerifyCodeSerializer
    permission_classes: tuple[type[AllowAny]] = AllowAny,

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
    permission_classes: tuple[type[AllowAny]] = AllowAny,

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
    permission_classes: tuple[type[IsAuthenticated]] = IsAuthenticated,

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

        serializer: UsersMeSerializer = self.get_serializer(
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


class ChangePasswordView(GenericAPIView):
    serializer_class: Type[ChangePasswordSerializer] = ChangePasswordSerializer
    permission_classes: tuple[type[IsAuthenticated]] = IsAuthenticated,

    def put(self, request: "Request", *args, **kwargs) -> Response:
        if not request.user.is_active:
            return Response(
                data={"detail": "User is inactive."},
                status=HTTP_400_BAD_REQUEST
            )

        serializer: ChangePasswordSerializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user: UserModel = UserService.authenticate(email_or_phone_number=request.user.email,
                                                   password=serializer.validated_data["old_password"])

        user.set_password(raw_password=serializer.validated_data["new_password"])
        user.save()
        update_session_auth_hash(request=request, user=user)

        tokens: dict[str, str] = UserService.create_tokens(user=user)

        return Response(
            data=tokens,
            status=HTTP_200_OK
        )


class ForgotPasswordView(GenericAPIView):
    permission_classes: tuple[Type[AllowAny]] = AllowAny,
    serializer_class: Type[ForgotPasswordSerializer] = ForgotPasswordSerializer

    def post(self, request: "Request", *args, **kwargs) -> Response:
        serializer: ForgotPasswordSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email: str = serializer.validated_data["email"]

        try:
            otp_code, otp_secret = generate_otp(phone_number_or_email=email)
            result: Literal[200, 400] = send_email(email=email, otp_code=otp_code)
            if result == 400:
                redis_conn.delete(f"{email}:otp")
                return Response(data={"detail": "Failed to send OTP Code"}, status=HTTP_400_BAD_REQUEST)
        except:
            otp_secret: str = redis_conn.get(f"{email}:otp_secret").decode()

        return Response(data={
            "email": email,
            "otp_secret": otp_secret
        })


class ForgotPasswordVerifyView(GenericAPIView):
    permission_classes: tuple[Type[AllowAny]] = AllowAny,
    serializer_class: Type[ForgotPasswordVerifySerializer] = ForgotPasswordVerifySerializer

    def post(self, request: "Request", *args, **kwargs) -> Response:
        serializer = self.get_serializer(
            data=request.data,
            context={"otp_secret": kwargs.get("otp_secret")})

        serializer.is_valid(raise_exception=True)

        email: str = serializer.validated_data["email"]
        otp_code: str = serializer.validated_data["otp_code"]
        otp_secret: str = serializer.validated_data["otp_secret"]

        try:
            check_otp(phone_number_or_email=email, otp_code=otp_code, otp_secret=otp_secret)
        except OTPException:
            return Response(
                data={"message": "Incorrect otp_code."},
                status=HTTP_400_BAD_REQUEST)

        redis_conn.delete(f"{email}:otp")
        redis_conn.delete(f"{email}:otp_secret")

        token_hash: str = make_password(password=token_urlsafe())
        redis_conn.set(token_hash, email, ex=2 * 60 * 60)

        return Response(data={"token": token_hash}, status=HTTP_200_OK)


class ResetPasswordView(GenericAPIView):
    permission_classes: tuple[Type[AllowAny]] = AllowAny,
    serializer_class: Type[ResetPasswordSerializer] = ResetPasswordSerializer

    def patch(self, request: "Request", *args, **kwargs) -> Response:
        serializer: ResetPasswordSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_hash: str = serializer.validated_data["token"]
        email: bytes = redis_conn.get(name=token_hash)
        if email is None:
            return Response(data={"detail": "Invalid Token."}, status=HTTP_400_BAD_REQUEST)
        queryset: "QuerySet[UserModel]" = UserModel.objects.filter(email=email.decode(), is_verified=True)
        if not queryset.exists():
            return Response(data={"detail": "Email not found."}, status=HTTP_400_BAD_REQUEST)

        user: UserModel | None = queryset.filter(is_active=True).first()

        if user is None:
            return Response(data={"detail": "Active user with such email not found."}, status=HTTP_400_BAD_REQUEST)

        password: str = serializer.validated_data["password"]

        if user.check_password(raw_password=password):
            return Response(data={"detail": "The new password can not be the same as the old password."},
                            status=HTTP_400_BAD_REQUEST)

        user.set_password(raw_password=password)
        user.save()

        update_session_auth_hash(request=request, user=user)
        tokens: dict[str, str] = UserService.create_tokens(user=user)
        redis_conn.delete(token_hash)
        return Response(data=tokens, status=HTTP_200_OK)
