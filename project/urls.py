from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from apps.account.views import AllUserRetrieveUpdateDestroyView, AllUserView

urlpatterns = [
    path('secret/', admin.site.urls),
    path('admin/alluser/', AllUserView.as_view(), name="All_Users"),
    path('admin/user/<int:pk>/', AllUserRetrieveUpdateDestroyView.as_view(), name="Admin_User_Update"),
    path('api/auth/', include('apps.account.urls')),
    path('api/datasystem/', include("apps.datasystem.urls")),
    path('api/payment/', include('apps.payment.urls')),
    path("api/dashboard/", include('apps.dashboard.urls'))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "PEOLLO ADMIN PORTAL"
admin.site.site_title = "PEOLLO ADMIN PORTAL"
admin.site.index_title = "WELCOME TO PEOLLO ADMIN PORTAL"