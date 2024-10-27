from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class BaseEnum(Enum):
    @classmethod
    def choices(cls) -> list[tuple["Any", str]]:
        return [(choice.value, choice.name) for choice in cls]

    @classmethod
    def values(cls) -> list:
        return [choice.value for choice in cls]


class UserRole(BaseEnum):
    """ Don't change the role name here. It will be used in permission system. """
    BUYER: str = "buyer"
    SELLER: str = "seller"
    ADMIN: str = "admin"


class PolicyNameEnum(BaseEnum):
    BUYER_POLICY: str = "buyer_policy"
    SELLER_POLICY: str = "seller_policy"
    ADMIN_POLICY: str = "admin_policy"
