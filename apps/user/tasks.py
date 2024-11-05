import logging
from smtplib import SMTPException
from typing import Literal

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string


@shared_task
def send_welcome_email(user_email: str) -> None:
    send_mail(
        subject="Xush kelibsiz!",
        message="Bizning platformaga xush kelibsiz!",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False
    )


@shared_task
def send_email(email: str, otp_code: str) -> Literal[200, 400]:
    message: str = render_to_string(template_name="emails/email_template.html", context={
        "email": email,
        "otp_code": otp_code
    })

    email_message: EmailMessage = EmailMessage(
        subject="Xizmatimizga xush kelibsiz!",
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[email]
    )
    email_message.content_subtype = "html"

    try:
        email_message.send(fail_silently=False)
        return 200
    except SMTPException:
        logging.error(msg="SMTP Error occurred: ", exc_info=True)
        return 400
    except OSError:
        logging.error(msg="Network Error: ", exc_info=True)
        return 400
    except:
        logging.error(msg="An Error occurred: ", exc_info=True)
        return 400
