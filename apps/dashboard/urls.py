from django.urls import path
from apps.dashboard.views import AdminDashboardViews, UserDashboardViews


urlpatterns = [
    path('card-data/', AdminDashboardViews.as_view(), name="card-data"),
    path('user/card-data/', UserDashboardViews.as_view(), name="user-card-data")
]
