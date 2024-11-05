from django.urls import path, include

from .views import SignUpView, VerifyView, LoginView

urlpatterns = [
    path("register/", include([
        path("", SignUpView.as_view()),
        path("verify/<str:otp_secret>/", VerifyView.as_view())]
    )),
    path("login/", LoginView.as_view())
]
