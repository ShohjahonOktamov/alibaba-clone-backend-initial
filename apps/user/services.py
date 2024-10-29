import random
import string
import uuid
from secrets import token_urlsafe

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from redis import Redis

from apps.share.exceptions import OTPException


class OTPService:
    @classmethod
    def get_redis_conn(cls) -> Redis:
        return Redis.from_url(settings.REDIS_URL)

    @classmethod
    def generate_otp(
            cls,
            phone_number: str,
            expire_in: int = 120,
            check_if_exists: bool = True
    ) -> tuple[str, str]:
        redis_conn: Redis = cls.get_redis_conn()
        otp_code: str = "".join(random.choices(population=string.digits, k=6))
        secret_token: str = token_urlsafe()
        otp_hash: str | bytes = make_password(f"{secret_token}:{otp_code}")
        key: str = f"{phone_number}:otp"

        if check_if_exists and redis_conn.exists(key):
            ttl: int = redis_conn.ttl(key)
            raise OTPException(
                _("You have a valid OTP code. Please try again in {ttl} seconds.").format(ttl=ttl)
            )

        redis_conn.set(name=key, value=otp_hash, ex=expire_in)
        return otp_code, secret_token

    @classmethod
    def check_otp(cls, phone_number: str, otp_code: str, otp_secret: str) -> None:
        redis_conn: Redis = cls.get_redis_conn()
        stored_hash: bytes = redis_conn.get(f"{phone_number}:otp")

        if not stored_hash or not check_password(f"{otp_secret}:{otp_code}", stored_hash.decode()):
            raise OTPException(_("Yaroqsiz OTP kodi."))

    @classmethod
    def generate_token(cls) -> str:
        return str(uuid.uuid4())
