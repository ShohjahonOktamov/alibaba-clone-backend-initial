import random
import string
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from redis import Redis
from user.models import Group
from user.models import Policy

from .exceptions import OTPException

if TYPE_CHECKING:
    from typing import Type
    from django.contrib.auth.models import AbstractBaseUser

UserModel: "Type[AbstractBaseUser]" = get_user_model()

redis_conn: Redis = Redis.from_url(settings.REDIS_URL)


def add_permissions(obj: UserModel | Group | Policy, permissions: list[str]) -> None:
    def get_permission(permission: str) -> list[Permission]:
        app_label, codename = permission.split('.')
        try:
            model: str = codename.split('_')[1]
            content_type, created = ContentType.objects.get_or_create(app_label=app_label, model=model)
            permission, created = Permission.objects.get_or_create(codename=codename, content_type=content_type)
        except (IndexError, ContentType.DoesNotExist):
            permission, created = Permission.objects.get_or_create(
                codename=codename
            )
        return permission

    if isinstance(obj, UserModel):
        obj.user_permissions.clear()
        obj.user_permissions.add(*map(get_permission, permissions))
    elif isinstance(obj, (Group, Policy)):
        obj.permissions.clear()
        obj.permissions.add(*map(get_permission, permissions))


def generate_otp(phone_number_or_email: str, expire_in: int = 120, check_if_exists: bool = True) -> tuple[
                                                                                                        str, str] | None:
    if check_if_exists and redis_conn.exists(f"{phone_number_or_email}:otp_secret"):
        ttl: int = redis_conn.ttl(f"{phone_number_or_email}:otp_secret")
        raise OTPException(
            _("You have a valid OTP code. Please try again in {ttl} seconds.").format(ttl=ttl)
        )

    otp_code: str = "".join(random.choices(population=string.digits, k=6))
    secret_token: str = token_urlsafe()
    redis_conn.set(name=f"{phone_number_or_email}:otp_secret", value=secret_token, ex=expire_in)
    otp_hash: str | bytes = make_password(password=f"{secret_token}:{otp_code}")
    key: str = f"{phone_number_or_email}:otp"
    redis_conn.set(name=key, value=otp_hash, ex=expire_in)
    print(otp_code, secret_token)
    return otp_code, secret_token


def send_email(email: str, otp_code: str) -> None:
    subject: str = "Welcome to Our Service!"
    message: str = render_to_string(template_name="emails/email_template.html", context={
        "email": email,
        "otp_code": otp_code
    })

    email: EmailMessage = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[email]
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)


def check_otp(phone_number_or_email: str, otp_code: str, otp_secret: str) -> None:
    stored_hash: bytes = redis_conn.get(f"{phone_number_or_email}:otp")

    if not check_password(password=f"{otp_secret}:{otp_code}", encoded=stored_hash.decode()):
        raise OTPException(detail="Incorrect otp_code.")
