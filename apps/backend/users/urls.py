from django.urls import path
from users.views import (RegisterView,
                         ActivateAccountView,
                         MeView,
                         LogoutView,
                         PasswordResetRequestView,
                         PasswordResetConfirmView,
                         LoginView,
                         RefreshView, ResendActivationView, UpdatePasswordInProfileView,
                         UpdateEmailInProfileView, EmailChangeConfirmView)
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<str:uidb64>/<str:token>/", ActivateAccountView.as_view(), name="activate"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshView.as_view(), name="token_refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("reset/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('me/', MeView.as_view(), name='me'),
    path("me/password/", UpdatePasswordInProfileView.as_view(), name="change_password"),
    path("me/email/", UpdateEmailInProfileView.as_view(), name="change_email"),
    path("email-change/confirm/<str:token>/", EmailChangeConfirmView.as_view(), name="email_change_confirm"),
    path("resend-activation/", ResendActivationView.as_view(), name="resend_activation"),
]



app_name = "users"
