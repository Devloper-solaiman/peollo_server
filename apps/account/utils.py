import random
from django.core.mail import EmailMessage
from google.auth.transport import requests
from google.oauth2 import id_token
from apps.account.models import User, OneTimePassword
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers


def generateOtp():
    otp = ""
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp


def send_code_to_user(email):
    otp_code = generateOtp()
    subject = f"passcode-{otp_code}"
    print(otp_code)
    user = User.objects.get(email=email)
    current_site = "peollo.io"
    frontend_url = f"{settings.FRONTEND_URL}/verify?otp_code={otp_code}"
    email_body = f"Thanks for sign up on {current_site}.\nPlease verify your email with the one time passcode\nYour passcode-{otp_code}\n Or you can try using below link\n{frontend_url}"
    from_email = settings.DEFAULT_FROM_EMAIL
    OneTimePassword.objects.create(user=user, code=otp_code)
    send_email = EmailMessage(subject=subject, body=email_body, from_email=from_email, to=[email])
    send_email.send(fail_silently=True)


class Google():

    @staticmethod
    def validate(access_token):
        if isinstance(access_token, dict) and "access_token" in access_token:
            access_token = access_token["access_token"]
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request())
            print(id_info)
            if "https://accounts.google.com" in id_info['iss']:
                print("true hoice", id_info)
                return id_info
        except ValueError:
            raise serializers.ValidationError("The token is invalid or has expired")
        

def login_scocial_user(email, password):
    user = authenticate(email=email, password=password)
    user_tokens = user.tokens()
    return {
            'email': user.email,
            "access_token": str(user_tokens.get("access_token")),
            "refresh_token": str(user_tokens.get("refresh"))
        }


def register_social_user(provider, email, first_name, last_name):
    user = User.objects.filter(email=email)

    if user.exists():
        if provider == user[0].auth_provider:
            result = login_scocial_user(email, settings.SOCIAL_AUTH_PASSWORD)
            result = result
        else:
            raise AuthenticationFailed(
                detail=f"Please continue your login with {user[0].auth_provider}"
            )
    else:
        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'credit': 0.0
        }
        register_user = User.objects.create(**new_user)
        register_user.set_password(settings.SOCIAL_AUTH_PASSWORD)
        register_user.auth_provider = provider
        register_user.is_active = True
        register_user.save()
        result = login_scocial_user(register_user.email, settings.SOCIAL_AUTH_PASSWORD)
    return result


def send_normal_email(data):
    email = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )

    email.send()