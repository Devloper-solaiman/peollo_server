from celery import shared_task
from apps.datasystem.models import DataEntry
from django.contrib.auth.models import User


@shared_task
def process_databatch(user_id, entries_batch):
    try: 
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User Doesn't exists"}


    data_entries = [DataEntry(user=user, **entry) for entry in entries_batch]
    DataEntry.objects.bulk_create(data_entries)
    
    return f"Processed id for {user_id} with {len(entries_batch)} entries"




