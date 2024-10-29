from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, ChoiceField, ValidationError, CharField

from .models import BuyerUser, SellerUser, Group, Policy

if TYPE_CHECKING:
    from typing import Type, Any
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


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
