from django.shortcuts import render
from django.conf import settings
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import smart_str, force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import generics, status, views
from apps.account.serializers import (
                                      UserRegistrationSerializer, 
                                      UserLoginSerializer,
                                      GoogleSignInSerializer,
                                      PasswordResetRequestSerializer,
                                      SetNewPasswordSerializer,
                                      ChangePasswordSerializer,
                                      UserProfileSerializer,
                                      UserUpdateSerializer,
                                      AdminUserUpdateSerializer,
                                      AllUsersSerializers
                                      )
from apps.account.utils import send_code_to_user
from apps.account.models import User, OneTimePassword
        

class RegisterUserView(generics.GenericAPIView):
    serializer_class = UserRegistrationSerializer
    authentication_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            with transaction.atomic():
                validated_data = serializer.validated_data  
                user = serializer.save(validated_data)
                user.save()
                send_code_to_user(validated_data['email'])
                return Response({'message': "A passcode has been sent to your email"}, 
                                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserEmail(generics.GenericAPIView):
    authentication_classes = []
    
    def post(self, request):
        otp_code = request.data.get('otp')
        try:
            user_code_obj = OneTimePassword.objects.get(code=otp_code)
            user = user_code_obj.user 

            if not user.is_active and user.role == "USER":
                user.is_active = True
                user.save()
                return Response({"message": "Email Succesfully Verified"}, status=status.HTTP_200_OK)
            elif not user.is_active and user.role == "ADMIN":
                user.is_active = True
                user.is_staff = True
                user.save()
                return Response({"message": "Email Succesfully Verified"}, status=status.HTTP_200_OK)
            elif not user.is_active and user.role == "SUPER_ADMIN":
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.save()
                return Response({"message": "Email Succesfully Verified"}, status=status.HTTP_200_OK)
            return Response({"message": "Code is Invalid or User Already Exists"}, status=status.HTTP_204_NO_CONTENT)
        
        except OneTimePassword.DoesNotExist:
            return Response({"message": "Passcode not provided"})


class GoogleSignInView(generics.GenericAPIView):
    serializer_class = GoogleSignInSerializer
    authentication_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # print("data hocce--->", data)
        return Response(data, status=status.HTTP_200_OK)


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    authentication_classes = []
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetRquestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            print(user)
            token = default_token_generator.make_token(user)
            print(token)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            print(uid)
            reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            # Send email
            context = {
                'reset_link': reset_link
            }

            email_subject = "Password Reset Request"
            email_body = render_to_string('resetpass_email.html', context)
            
            email = EmailMultiAlternatives(email_subject, '', to=[user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()

            return Response({"detail": "Password reset email has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self, queryset=None):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Profile View
class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
   
    def get_object(self):
        queryset = User.objects.get(email=self.request.user.email)
        return queryset


class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        return User.objects.get(email=self.request.user.email)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_instance = serializer.save()

        email_changed = serializer.context.get('email_changed')
        if email_changed:
            return Response({
                "message": "A verification email has been sent to your new email address. "
                           "Please verify to complete the email update."
            }, status=status.HTTP_200_OK)

        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyEmailChangeView(views.APIView):
    authentication_classes = []

    def get(self, request, user_id, token):
        
        cached_email = cache.get(f'email_change_{user_id}')
        cached_token = cache.get(f'email_change_token_{user_id}')

        if cached_email and cached_token == token:
            try:
                user = User.objects.get(id=user_id)
                user.email = cached_email
                user.save()

                cache.delete(f"email_change_{user_id}")
                cache.delete(f"email_change_token_{user_id}")

                return Response({"message": "Email updated successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class AllUserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        # print(user)
        # print(request.user.role)
        is_blocked_value = request.data.get("is_blocked")
        is_blocked_value = str(is_blocked_value)
        # print(type(is_blocked_value))

        if (
            user.role == "USER" and 
            request.data.get("role") == "ADMIN" and 
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # USER to ADMIN
            user.role = "ADMIN"
            user.is_staff = True
            user.save()
            user.refresh_from_db()

        elif (
            user.role in ["USER", "ADMIN"] and
            request.data.get("role") == "SUPER_ADMIN" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # USER/ADMIN to SUPER_ADMIN (Only SUPER_ADMIN can promote)
            user.role = "SUPER_ADMIN"
            user.is_staff = True
            user.is_superuser = True
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "ADMIN" and
            request.data.get("role") == "USER" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # ADMIN to USER (Only ADMIN can demote)
            user.role = "USER"
            user.is_staff = False
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "SUPER_ADMIN" and
            request.data.get("role") == "USER" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # SUPER_ADMIN to USER (Only SUPER_ADMIN can demote)
            user.role = "USER"
            user.is_superuser = False
            user.is_staff = False
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "SUPER_ADMIN" and
            request.data.get("role") == "ADMIN" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # SUPER_ADMIN to ADMIN (Only SUPER_ADMIN can demote)
            user.role = "ADMIN"
            user.is_superuser = False
            user.is_staff = True
            user.save()
            user.refresh_from_db()
        
        if not user.is_blocked and is_blocked_value == "True":
            user.is_blocked = True
            user.is_active = False
            
            if user.role in ["ADMIN", "SUPER_ADMIN"]:
                user.is_staff = False
                
            user.save()
            user.refresh_from_db()
        elif user.is_blocked and is_blocked_value == "False":
            user.is_blocked = False
            user.is_active = True
            if user.role in ["ADMIN", "SUPER_ADMIN"]:
                user.is_staff = True
                
            user.save()
            user.refresh_from_db()
        # else:
        #     return Response({"error": "You do not have permission to perform this action."},
        #                     status=status.HTTP_403_FORBIDDEN)

        response = super().update(request, *args, **kwargs)
        return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        # print(request.user.role)
        if (
            user.role == "USER" and 
            request.data.get("role") == "ADMIN" and 
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # USER to ADMIN
            user.role = "ADMIN"
            user.is_staff = True
            user.save()
            user.refresh_from_db()

        elif (
            user.role in ["USER", "ADMIN"] and
            request.data.get("role") == "SUPER_ADMIN" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # USER/ADMIN to SUPER_ADMIN (Only SUPER_ADMIN can promote)
            user.role = "SUPER_ADMIN"
            user.is_staff = True
            user.is_superuser = True
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "ADMIN" and
            request.data.get("role") == "USER" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # ADMIN to USER (Only ADMIN can demote)
            user.role = "USER"
            user.is_staff = False
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "SUPER_ADMIN" and
            request.data.get("role") == "USER" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # SUPER_ADMIN to USER (Only SUPER_ADMIN can demote)
            user.role = "USER"
            user.is_superuser = False
            user.is_staff = False
            user.save()
            user.refresh_from_db()

        elif (
            user.role == "SUPER_ADMIN" and
            request.data.get("role") == "ADMIN" and
            request.user.role in ["ADMIN", "SUPER_ADMIN"]
        ):
            # SUPER_ADMIN to ADMIN (Only SUPER_ADMIN can demote)
            user.role = "ADMIN"
            user.is_superuser = False
            user.is_staff = True
            user.save()
            user.refresh_from_db()
        
        # else:
        #     return Response({"error": "You do not have permission to Change the user role."},
        #                     status=status.HTTP_403_FORBIDDEN)
        
        is_blocked_value = request.data.get("is_blocked")
        is_blocked_value = str(is_blocked_value)
        # print(type(is_blocked_value))

        if not user.is_blocked and is_blocked_value == "True":
            user.is_blocked = True
            user.is_active = False
            
            if user.role in ["ADMIN", "SUPER_ADMIN"]:
                user.is_staff = False
                
            user.save()
            user.refresh_from_db()
        
        elif user.is_blocked and is_blocked_value == "False":
            print("elif logic er modde")
            # print("before--->", user.is_active, user.is_staff, user.is_blocked)
            user.is_blocked = False
            user.is_active = True
            if user.role in ["ADMIN", "SUPER_ADMIN"]:
                user.is_staff = True
                
            user.save()
            # print("after--->", user.is_active, user.is_staff, user.is_blocked)
            user.refresh_from_db()
        

        response = super().partial_update(request, *args, **kwargs)
        return Response({"message": "user partially updated successfully"}, status=status.HTTP_200_OK)
    

class AllUserView(generics.ListAPIView):
    queryset = User.objects.exclude(email="devcluster24@gmail.com")
    serializer_class = AllUsersSerializers
    permission_classes = [IsAdminUser, IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return Response(response.data, status=status.HTTP_200_OK)

