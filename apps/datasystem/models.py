from django.db import models
from django.utils import timezone
from apps.account.models import User


class DataEntry(models.Model):
    peolloid = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    company_name_for_emails = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    email_status = models.CharField(max_length=255, blank=True)
    email_confidence = models.CharField(max_length=255, blank=True)
    primary_email_catch_allstatus = models.CharField(max_length=255, blank=True)
    primary_email_last_verified_at = models.CharField(max_length=255, blank=True)
    seniority = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    contact_owner = models.CharField(max_length=255, blank=True)
    first_phone = models.CharField(max_length=255, blank=True)
    work_direct_phone = models.CharField(max_length=255, blank=True)
    home_phone = models.CharField(max_length=255, blank=True)
    mobile_phone = models.CharField(max_length=255, blank=True)
    corporate_phone = models.CharField(max_length=255, blank=True)
    other_phone = models.CharField(max_length=255, blank=True)
    stage = models.CharField(max_length=255, blank=True)
    lists = models.CharField(max_length=255, blank=True)
    last_contacted = models.CharField(max_length=255, blank=True)
    account_owner = models.CharField(max_length=255, blank=True)
    employees = models.IntegerField(blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True)
    keywords = models.JSONField(blank=True, null=True)
    person_linkedin_url = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)
    company_linkedin_url = models.CharField(max_length=255, blank=True)
    facebook_url = models.CharField(max_length=255, blank=True)
    twitter_url = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    company_address = models.TextField(blank=True)
    company_city = models.CharField(max_length=255, blank=True)
    company_state = models.CharField(max_length=255, blank=True)
    company_country = models.CharField(max_length=255, blank=True)
    company_phone = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    technologies = models.JSONField(blank=True, null=True)
    annual_revenue = models.BigIntegerField(blank=True, null=True)
    total_funding = models.CharField(max_length=255, blank=True)
    latest_funding = models.CharField(max_length=255, blank=True)
    latest_funding_amount = models.CharField(max_length=255, blank=True)
    last_raised_at = models.CharField(max_length=255, blank=True)
    email_sent = models.CharField(max_length=255, blank=True)
    email_open = models.CharField(max_length=255, blank=True)
    email_bounced = models.CharField(max_length=255, blank=True)
    replied = models.CharField(max_length=255, blank=True)
    demoed = models.CharField(max_length=255, blank=True)
    number_of_retailed_locations = models.CharField(max_length=255, blank=True)
    apollo_contact_id = models.CharField(max_length=255, blank=True)
    apollo_account_id = models.CharField(max_length=255, blank=True)
    primary_email_source = models.CharField(max_length=255, blank=True)
    secondary_email = models.CharField(max_length=255, blank=True)
    secondary_email_source = models.CharField(max_length=255, blank=True)
    tertiary_email = models.CharField(max_length=255, blank=True)
    tertiary_email_source = models.CharField(max_length=255, blank=True)
    primary_intent_topic = models.CharField(max_length=255, blank=True)
    primary_intent_score = models.CharField(max_length=255, blank=True)
    secondary_intent_topic = models.CharField(max_length=255, blank=True)
    secondary_intent_score = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    

class UserDataPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    data = models.ForeignKey(DataEntry, on_delete=models.CASCADE, blank=True, null=True)
    is_purchased = models.BooleanField(default=False)
    purchase_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'data')


class SavedData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    data = models.ForeignKey(DataEntry, on_delete=models.CASCADE, blank=True, null=True)
    saved_at = models.DateTimeField(default=timezone.now)


class SavedList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    data = models.ForeignKey(DataEntry, on_delete=models.CASCADE, blank=True, null=True)
    folder_name = models.CharField(max_length=255, blank=True, null=True)
    saved_at = models.DateTimeField(default=timezone.now)
    last_modified_at = models.DateTimeField(auto_now=True)


class CsvImportHistroy(models.Model):
    total_records = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.DateTimeField(default=timezone.now)
    

class CsvExportHistory(models.Model):
    progress = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)
    credits = models.FloatField(default=0.0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    exported_by = models.DateTimeField(default=timezone.now)


