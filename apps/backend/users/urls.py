from django.urls import path
from users.views import (RegisterView,
                         ActivateAccountView,
                         MeView,
                         LogoutView,
                         PasswordResetRequestView,
                         PasswordResetConfirmView, AddressView, LoginView)
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<str:uidb64>/<str:token>/", ActivateAccountView.as_view(), name="activate"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("reset/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('me/', MeView.as_view(), name='me'),
    path("me/address/", AddressView.as_view(), name="address")
]



app_name = "users"
