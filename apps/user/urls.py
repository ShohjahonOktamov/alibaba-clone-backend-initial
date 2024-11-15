from django.urls import path, include

from .views import SignUpView, VerifyView, LoginView, UserMeView, ChangePasswordView, ForgotPasswordView, \
    ForgotPasswordVerifyView, ResetPasswordView, LogoutView

urlpatterns = [
    path("register/", include([
        path("", SignUpView.as_view()),
        path("verify/<str:otp_secret>/", VerifyView.as_view())]
    )),
    path("login/", LoginView.as_view()),
    path("me/", UserMeView.as_view()),
    path("change/password/", ChangePasswordView.as_view()),
    path("password/", include([
        path("forgot/", include([
            path("", ForgotPasswordView.as_view()),
            path("verify/<str:otp_secret>/", ForgotPasswordVerifyView.as_view()),
        ])),
        path("reset/", ResetPasswordView.as_view())
    ]
    )),
    path("logout/", LogoutView.as_view())
]
