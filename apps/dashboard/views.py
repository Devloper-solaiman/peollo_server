from rest_framework.response import Response
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.datasystem.models import (
                                    DataEntry, 
                                    UserDataPurchase, 
                                    User, SavedData,
                                    SavedList
                                    )


class AdminDashboardViews(views.APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        total_data = DataEntry.objects.all().count()
        sale_data = UserDataPurchase.objects.all().count()
        user = User.objects.all().count()
     
        return Response({
                         "total": total_data,
                         "sale_data": sale_data,
                         "user": user
                        },
                        status=status.HTTP_200_OK
                        )


class UserDashboardViews(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        total_data = DataEntry.objects.all().count()
        total_saved_data = SavedData.objects.filter(user=request.user).count()
        total_saved_list = SavedList.objects.filter(user=request.user).count()

        return Response(
            {
                "total_data": total_data,
                "total_saved_data": total_saved_data,
                "total_saved_list": total_saved_list
            },
            status=status.HTTP_200_OK
        )
