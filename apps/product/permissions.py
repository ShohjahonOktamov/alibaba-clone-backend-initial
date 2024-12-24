from typing import TYPE_CHECKING

from rest_framework.permissions import BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import View


class IsBuyer(BasePermission):
    def has_permission(self, request: "Request", view: "View") -> bool:
        return request.user.groups.filter(name="buyer").exists()
