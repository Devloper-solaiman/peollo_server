from django.urls import path
from apps.account.views import (
                                RegisterUserView, 
                                VerifyUserEmail,
                                UserLoginView,
                                GoogleSignInView,
                                PasswordResetRquestView,
                                SetNewPasswordView,
                                UserProfileView,
                                UserUpdateView,
                                ChangePasswordView,
                                VerifyEmailChangeView
                                )


urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify_email/', VerifyUserEmail.as_view(), name="verify"),
    path('login/', UserLoginView.as_view(), name="login"),
    path('me/', UserProfileView.as_view(), name="user_profile"),
    path('me/update/', UserUpdateView.as_view(), name="user_profile"),
    path('google/signin/', GoogleSignInView.as_view(), name="Google_signin"),
    path('password-reset/', PasswordResetRquestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', SetNewPasswordView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),
    path('verify-email-change/<int:user_id>/<str:token>/', VerifyEmailChangeView.as_view(), name='verify-email-change'),   
]
