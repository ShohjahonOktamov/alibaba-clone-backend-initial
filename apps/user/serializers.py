from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from redis import Redis
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer, ChoiceField, ValidationError, CharField, Serializer

from .models import BuyerUser, SellerUser, Group, Policy

if TYPE_CHECKING:
    from typing import Type, Any
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


class UserSerializer(ModelSerializer):
    confirm_password = CharField(write_only=True)
    user_trade_role = ChoiceField(choices=("seller", "buyer"), required=True)

    class Meta:
        model: "Type[UserModel]" = UserModel
        fields: tuple[
            str] = "id", "email", "phone_number", "password", "confirm_password", \
            "first_name", "last_name", "gender", "created_by", "user_trade_role"

        extra_kwargs: dict[str:dict[str, bool]] = {
            "id": {"read_only": True},
            "password": {"write_only": True},
        }

    def create(self, validated_data: "dict[str, Any]") -> UserModel:
        user_trade_role: str = validated_data.pop("user_trade_role")
        validated_data.pop("confirm_password")

        user: UserModel = UserModel.objects.create_user(**validated_data)

        if user_trade_role == "buyer":
            BuyerUser.objects.create(user=user)

            buyer_group: Group = Group.objects.get(name="buyer")
            buyer_policy: Policy = Policy.objects.get(name="buyer_policy")

            user.groups.add(buyer_group)
            user.policies.add(buyer_policy)
        elif user_trade_role == "seller":
            SellerUser.objects.create(user=user)

            seller_group: Group = Group.objects.get(name="seller")
            seller_policy: Policy = Policy.objects.get(name="seller_policy")

            user.groups.add(seller_group)
            user.policies.add(seller_policy)

        return user

    def is_valid(self, *, raise_exception: bool = False) -> bool:
        valid: bool = super().is_valid(raise_exception=raise_exception)

        confirm_password: str | None = self.initial_data.get("confirm_password")
        password: str | None = self.initial_data.get("password")

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        user_trade_role: str | None = self.initial_data.get("user_trade_role")

        if user_trade_role not in ("seller", "buyer"):
            self._errors["user_trade_role"]: list[str] = ["user_trade_role must be either 'seller' or 'buyer'."]
            if raise_exception:
                raise ValidationError(self.errors)
            return False

        return valid


class VerifyCodeSerializer(Serializer):
    phone_number = CharField(min_length=6, max_length=13, required=True)
    otp_code = CharField(max_length=6, required=True)

    def validate(self, data: dict[str, str]) -> dict[str, str] | None:
        otp_secret: str | None = self.context.get("otp_secret")  # get the otp_secret

        if otp_secret is None:
            raise ValidationError(
                detail={"message": "otp_secret is required."},
                code="otp_secret_not_provided")

        if otp_secret == "" or otp_secret.isspace():
            raise NotFound(
                detail={"message": "otp_secret may not be blank."},
                code="empty_otp_secret")

        phone_number: str | None = data.get("phone_number")  # get the phone_number from data

        # if the phone_number is not provided
        if phone_number is None:
            raise ValidationError(
                detail={"message": "phone_number is required."},
                code="phone_number_not_provided")

        # if the phone_number has invalid format
        if not phone_number.startswith('+') or not phone_number[1:].isdigit():
            raise ValidationError(
                detail={"message": "Invalid phone_number."},
                code="invalid_phone_number")

        if UserModel.objects.filter(phone_number=phone_number, is_verified=True).exists():
            raise NotFound(
                detail="Unverified User not found.",
                code="user_is_already_verified"
            )

        otp_code: str | None = data.get("otp_code")  # get the otp_code

        # if the otp_code is not provided
        if otp_code is None:
            raise ValidationError(
                detail={"message": "otp_code is required."},
                code="otp_code_not_provided")

        # if the otp_code field is empty
        if otp_code == "" or otp_code.isspace():
            raise ValidationError(
                detail={"message": "otp_code can not be blank."},
                code="empty_otp_code")

        # if the length of the otp_code is not equal to 6 or if it does not fully consist of digits
        if len(otp_code) != 6 or not otp_code.isdigit():
            raise ValidationError(
                detail={"message": "Invalid otp_code format."},
                code="invalid_otp_code_format"
            )

        return data
