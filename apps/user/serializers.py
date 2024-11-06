import re
from typing import TYPE_CHECKING, Type, Any, Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from redis import Redis
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer, ChoiceField, ValidationError, CharField, Serializer, \
    SerializerMethodField

from .models import BuyerUser, SellerUser, Group, Policy

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.db.models import QuerySet

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


class UserSerializer(ModelSerializer):
    confirm_password = CharField(write_only=True)
    user_trade_role = ChoiceField(choices=("seller", "buyer"), required=True)

    class Meta:
        model: Type[UserModel] = UserModel
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


class LoginSerializer(Serializer):
    email_or_phone_number = CharField(required=True, min_length=6, max_length=255)
    password = CharField(write_only=True, required=True)

    def validate(self, data: dict[str, str]) -> dict[str, str]:
        email_or_phone_number: str = data["email_or_phone_number"]

        if re.match(pattern=r"[^@]+@[^@]+\.[^@]+", string=email_or_phone_number):
            return data

        if re.match(pattern=r"^\+?1?\d{6,13}$", string=email_or_phone_number):
            return data

        raise ValidationError("Enter a valid phone number or email address.")


class BuyerUserSerializer(ModelSerializer):
    class Meta:
        model: Type[BuyerUser] = BuyerUser
        fields: tuple[
            str] = "photo", "bio", "birth_date", "country", "city", "district", \
            "street_address", "postal_code", "second_phone_number", "building_number", "apartment_number"


class SellerUserSerializer(ModelSerializer):
    class Meta:
        model: Type[SellerUser] = SellerUser
        fields: tuple[
            str] = "company", "photo", "bio", "birth_date", "country", "city", "district", \
            "street_address", "postal_code", "second_phone_number", "building_number", "apartment_number"


class UsersMeSerializer(ModelSerializer):
    user_trade_role = SerializerMethodField(method_name="get_user_trade_role")
    trader_user = SerializerMethodField(method_name="get_trader_user")

    class Meta:
        model: Type[UserModel] = UserModel
        fields: tuple[
            str] = "id", "first_name", "last_name", "phone_number", "email", "gender", "user_trade_role", "trader_user"
        extra_kwargs: dict[str:dict[str, bool]] = {
            "id": {"read_only": True},
            "user_trade_role": {"read_only": True}
        }

    def get_user_trade_role(self, instance: UserModel) -> Literal["buyer", "seller"] | None:
        user_groups: "QuerySet[str]" = instance.groups.values_list("name", flat=True)
        if "buyer" in user_groups:
            return "buyer"
        elif "seller" in user_groups:
            return "seller"
        return None

    def get_trader_user(self, instance: UserModel) -> dict[str, Any | None] | None:
        buyer_user: BuyerUser = BuyerUser.objects.filter(user=instance).first()
        if buyer_user is not None:
            return BuyerUserSerializer(instance=buyer_user).data

        seller_user: SellerUser = SellerUser.objects.filter(user=instance).first()
        if seller_user is not None:
            return SellerUserSerializer(instance=seller_user).data

        return None

    def to_representation(self, instance: UserModel) -> dict[str, Any | None]:
        representation: dict[str, Any | None] = super().to_representation(instance=instance)
        representation.pop("user_trade_role", None)
        trader_user_data: dict[str, Any | None] = representation.pop("trader_user", {})
        representation.update(trader_user_data)

        return representation


class ChangePasswordSerializer(Serializer):
    old_password = CharField(required=True)
    new_password = CharField(required=True)
    confirm_password = CharField(required=True)

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        if attrs["new_password"] != attrs["confirm_password"]:
            raise ValidationError(
                detail="The new password and the confirm passwords do not match.",
                code="new_and_confirm_passwords_do_not_match"
            )

        if attrs["old_password"] == attrs["new_password"]:
            raise ValidationError(
                detail="The new password can not be the same as the old password.",
                code="old_and_new_passwords_match"
            )

        validate_password(attrs["new_password"])

        return attrs
