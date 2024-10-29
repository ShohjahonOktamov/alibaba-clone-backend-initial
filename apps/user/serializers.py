from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, ChoiceField, ValidationError

from .models import BuyerUser, SellerUser, Group

if TYPE_CHECKING:
    from typing import Type, Any
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()


class UserSerializer(ModelSerializer):
    user_trade_role = ChoiceField(choices=("seller", "buyer"), required=True)

    class Meta:
        model: "Type[UserModel]" = UserModel
        fields: str = "__all__"
        extra_kwargs: dict[str:dict[str, bool]] = {"password": {"write_only": True}}

    def create(self, validated_data: "dict[str,Any]") -> UserModel:
        user_trade_role: str = validated_data.pop("user_trade_role")

        user: UserModel = UserModel.objects.create_user(**validated_data)

        if user_trade_role == "buyer":
            BuyerUser.objects.create(user=user)

            buyer_group: Group = Group.objects.get(name="buyer")
            user.groups.add(buyer_group)
        elif user_trade_role == "seller":
            SellerUser.objects.create(user=user)

            seller_group: Group = Group.objects.get(name="seller")
            user.groups.add(seller_group)

        return user

    def is_valid(self, *, raise_exception: bool = False) -> bool:
        valid: bool = super().is_valid(raise_exception=raise_exception)

        user_trade_role: str | None = self.initial_data.get("user_trade_role")
        if user_trade_role not in ("seller", "buyer"):
            self._errors["user_trade_role"]: list[str] = ["user_trade_role must be either 'seller' or 'buyer'."]
            if raise_exception:
                raise ValidationError(self.errors)
            return False

        return valid
