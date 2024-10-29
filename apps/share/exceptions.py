from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST

if TYPE_CHECKING:
    from django.utils.translation import lazy


class OTPException(APIException):
    status_code: int = HTTP_400_BAD_REQUEST
    default_detail: "lazy" = _("OTP verification failed.")
    default_code: str = "otp_failed"
