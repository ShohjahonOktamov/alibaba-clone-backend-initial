from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_welcome_email(user_email: str) -> None:
    send_mail(
        subject="Xush kelibsiz!",
        message="Bizning platformaga xush kelibsiz!",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False
    )
