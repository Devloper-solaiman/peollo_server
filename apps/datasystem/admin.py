from django.contrib import admin
from apps.datasystem.models import (
                                    DataEntry, SavedList, 
                                    SavedData, UserDataPurchase,
                                    CsvExportHistory, CsvImportHistroy
                                    )


admin.site.register(DataEntry)
admin.site.register(SavedData)
admin.site.register(SavedList)
admin.site.register(UserDataPurchase)
admin.site.register(CsvImportHistroy)
admin.site.register(CsvExportHistory)