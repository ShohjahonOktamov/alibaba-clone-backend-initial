from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from share.utils import generate_otp, send_email, redis_conn

from apps.share.exceptions import OTPException
from .serializers import UserSerializer

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractBaseUser
    from rest_framework.permissions import BasePermission
    from rest_framework.request import Request
    from rest_framework.response import Response

UserModel: "Type[AbstractBaseUser]" = get_user_model()


# Create your views here.

class SignUpView(APIView):
    serializer_class: "Type[UserSerializer]" = UserSerializer
    permission_classes: "tuple[type[BasePermission]]" = AllowAny,

    @staticmethod
    def post(request: "Request") -> "Response":
        serializer: UserSerializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            email: str = serializer.validated_data.get("email")
            phone_number: str = serializer.validated_data.get("phone_number")

            try:
                otp_code, otp_secret = generate_otp(phone_number_or_email=phone_number, check_if_exists=False)
                send_email(email=email, otp_code=otp_code)

            except OTPException:
                otp_secret: str = redis_conn.get(f"{email}:otp_secret").decode()

            return Response(data={
                "phone_number": phone_number,
                "otp_secret": otp_secret},
                status=HTTP_201_CREATED)

        return Response(data=serializer.errors,
                        status=HTTP_400_BAD_REQUEST)
