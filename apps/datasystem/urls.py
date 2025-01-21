from django.urls import path
from apps.datasystem.views import (
                                   UploadJsonBatchView, 
                                   DataEntryDetailView, 
                                   GetDataView,
                                   DataEntryDeleteView,
                                   NetNewData,
                                   DataPurchaseView,
                                   DataDownloadView,
                                   SavedListViews,
                                   GetAllSavedData,
                                   GetAllSavedListData,
                                   GetCompanyInfoView,
                                   AllFoderNameViews,
                                   ListFolderUpdateDeleteViews,
                                   CvImportHistoryViews,
                                   CvExportHistoryViews
                                   )


urlpatterns = [
    path("", GetDataView.as_view(), name="get_data"),
    path("delete-data/", DataEntryDeleteView.as_view(), name="Delete_data"),
    path("new/", NetNewData.as_view()),
    path("saved-data/list/", GetAllSavedData.as_view(), name="get_saved_data"),
    path("saved-list/", GetAllSavedListData.as_view(), name="get_saved_list_data"),
    path("upload/", UploadJsonBatchView.as_view(), name="upload_data"),
    path("<int:pk>/", DataEntryDetailView.as_view(), name="delete_data"),
    path('add-to-save-list/', SavedListViews.as_view(), name='save_list'),
    path('saved-data/', DataPurchaseView.as_view(), name='saved_data'),
    path('data-download/', DataDownloadView.as_view(), name='data_download'),
    path('companyinfo/', GetCompanyInfoView.as_view(), name="all-company"),
    path('folder_name/', AllFoderNameViews.as_view(), name='folder_name'),
    path("saved-list/<str:folder_name>/", ListFolderUpdateDeleteViews.as_view(), name='update-delete'),
    path("csvimport/", CvImportHistoryViews.as_view(), name="csv_import"),
    path("csvexport/", CvExportHistoryViews.as_view(), name="csv_export")
]
