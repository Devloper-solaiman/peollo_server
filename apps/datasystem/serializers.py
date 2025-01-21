from rest_framework import serializers
from apps.datasystem.models import (
                                    DataEntry, 
                                    SavedList, 
                                    SavedData, 
                                    UserDataPurchase,
                                    CsvImportHistroy,
                                    CsvExportHistory
                                    )
from apps.account.models import User
from django.db import transaction
from django.utils import timezone


class DataEntrySerializer(serializers.ModelSerializer):
    keywords = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    technologies = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    class Meta:
        model = DataEntry
        extra_kwargs = { 
                         "first_name": {'required': False},
                         "last_name": {'required': False},
                         "title": {'required': False},
                         "company": {'required': False},
                         "company_name_for_emails": {'required': False},
                         "email": {'required': False},
                         "email_status": {'required': False},
                         "email_confidence": {'required': False},
                         "primary_email_catch_allstatus": {'required': False},
                         "primary_email_last_verified_at": {'required': False},
                         "seniority": {'required': False},
                         "department": {'required': False},
                         "contact_owner": {'required': False},
                         "first_phone": {'required': False},
                         "work_direct_phone": {'required': False},
                         "home_phone": {'required': False},
                         "mobile_phone": {'required': False},
                         "corporate_phone": {'required': False},
                         "other_phone": {'required': False},
                         "stage": {'required': False},
                         "lists": {'required': False},
                         "last_contacted": {'required': False},
                         "account_owner": {'required': False},
                         "employees": {'required': False},
                         "industry": {'required': False},
                         "keywords": {'required': False},
                         "person_linkedin_url": {'required': False},
                         "website": {'required': False},
                         "company_linkedin_url": {'required': False},
                         "facebook_url": {'required': False},
                         "twitter_url": {'required': False},
                         "city": {'required': False},
                         "state": {'required': False},
                         "country": {'required': False},
                         "company_address": {'required': False},
                         "company_city": {'required': False},
                         "company_state": {'required': False},
                         "company_country": {'required': False},
                         "seo_description": {'required': False},
                         "technologies": {'required': False},
                         "annual_revenue": {'required': False},
                         "total_funding": {'required': False},
                         "latest_funding": {'required': False},
                         "latest_funding_amount": {'required': False},
                         "last_raised_at": {'required': False},
                         "email_sent": {'required': False},
                         "email_open": {'required': False},
                         "email_bounced": {'required': False},
                         "last_raised_at": {'required': False},
                         "replied": {'required': False},
                         "demoed": {'required': False},
                         "number_of_retailed_locations": {'required': False},
                         "apollo_contact_id": {'required': False},
                         "apollo_account_id": {'required': False},
                         "primary_email_source": {'required': False},
                         "secondary_email": {'required': False},
                         "secondary_email_source": {'required': False},
                         "tertiary_email": {'required': False},
                         "tertiary_email_source": {'required': False},
                         "primary_intent_topic": {'required': False},
                         "primary_intent_score": {'required': False},
                         "secondary_intent_topic": {'required': False},
                         "secondary_intent_score": {'required': False},
         }
        fields = [
                  "peolloid", "first_name", "last_name", "title", "company", 
                  "company_name_for_emails", "email", "email_status", 
                  "email_confidence", "primary_email_catch_allstatus", 
                  "primary_email_last_verified_at", "seniority", "department", 
                  "contact_owner", "first_phone", "work_direct_phone", 
                  "home_phone", "mobile_phone", "corporate_phone",
                  "other_phone", "stage", "lists", "last_contacted", 
                  "account_owner", "employees", "industry", "keywords", 
                  "person_linkedin_url", "website", "company_linkedin_url",
                  "facebook_url", "twitter_url", "city", "state", "country", 
                  "company_address", "company_city", "company_state", 
                  "company_country", "company_phone", "seo_description", "technologies",
                  "annual_revenue", "total_funding", "latest_funding", 
                  "latest_funding_amount", "last_raised_at", "email_sent", 
                  "email_open", "email_bounced", "replied", "demoed",
                  "number_of_retailed_locations", "apollo_contact_id", 
                  "apollo_account_id", "primary_email_source", 
                  "secondary_email", "secondary_email_source",
                  "tertiary_email", "tertiary_email_source", 
                  "primary_intent_topic", "primary_intent_score", 
                  "secondary_intent_topic", "secondary_intent_score",
                  "created_at"
                  ]
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)

        # Check if request and request.user exist and user is authenticated
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            if not UserDataPurchase.objects.filter(user=user, data=instance).exists():
                representation.pop("email", None)
                representation.pop("mobile_phone", None)
        else:
            representation.pop("email", None)
            representation.pop("mobile_phone", None)

        return representation

    
class BulkDataEntrySerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # folder_name = serializers.CharField(max_length=255, required=True)
    data = DataEntrySerializer(many=True)  # Array of data entries

    def create(self, validated_data):
        user = validated_data['user']
        entries_data = validated_data['data']
        data_entries = []
        imported_count = 0

        with transaction.atomic():
            for entry_data in entries_data:
                if DataEntry.objects.filter(email=entry_data.get('email')).exists():
                    continue
                entry_data['user'] = user
                data_entries.append(DataEntry(**entry_data))
            imported_count = len(data_entries)    
            DataEntry.objects.bulk_create(data_entries)
        
        CsvImportHistroy.objects.create(
                total_records=imported_count,
                uploaded_by=user,
                created_by=timezone.now()
            )
        return {"user": user, "data": entries_data}


    # def create(self, validated_data):
        # user = validated_data['user']
        # folder_name = validated_data['folder_name'] 
        # entries_data = validated_data['data']
        # data_entries = []
        # data_count = 0
        
        # import_history = CsvImportHistroy.objects.create(
        #     name=folder_name,
        #     uploaded_by=user,
        #     total_records=len(entries_data)
        # )

        # with transaction.atomic():
        #     for i, entry in enumerate(entries_data):
        #         entry['user'] = user
        #         data_entries.append(DataEntry(**entry))
                
        #         if (i + 1) % 1000 == 0:
        #             DataEntry.objects.bulk_create(data_entries)
        #             data_count += len(data_entries)
        #             data_entries = []

        #     if data_entries:
        #         DataEntry.objects.bulk_create(data_entries)
                # data_count += len(data_entries)

            # import_history.progress = int((data_count / len(entries_data)) * 100)
            # import_history.save()
    # user_id = validated_data.pop('user')
    # data_entries = validated_data.pop('data')
    # entries_to_create = []
    
    # for entry in data_entries:
    #     entry['user_id'] = user_id  # Set the user_id for each entry
    #     entries_to_create.append(DataEntry(**entry))  # Prepare for bulk_create

    #     DataEntry.objects.bulk_create(entries_to_create)

        # return {"user": user, "data": entries_data}


class DataSavedSerializer(serializers.ModelSerializer):
    data = DataEntrySerializer()

    class Meta:
        model = SavedData
        fields = '__all__'


class DataSavedListSerializer(serializers.ModelSerializer):
    data = DataEntrySerializer()
    
    class Meta:
        model = SavedList
        fields = '__all__'


class AllCompanyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataEntry
        fields = ['company']


class AllListSerializer(serializers.ModelSerializer):
    total_record = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = SavedList
        fields = ['folder_name', 'user', 'username', 'last_modified_at', 'total_record']
    
    def get_username(self, obj):
        return obj.user.first_name
    
    def get_total_record(self, obj):
        user = obj.user
        folder_name = obj.folder_name
        record_count = SavedList.objects.filter(user=user, folder_name=folder_name).count()
        return record_count

# class DataSystem(serializers.ModelSerializer):
#     user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
#     entries = DataEntrySerializer(many=True)

#     def create(self, validated_data):
#         user = validated_data['user']
#         data_entries = validated_data['data']

#         entries = []

#         for entry_data in data_entries:
#             entry = DataEntry(
#                 user=user,
#                 first_name=entry_data.get('first_name', ''),
#                 last_name=entry_data.get('last_name', ''),
#                 title=entry_data.get('title', ''),
#                 company=entry_data.get('company', ''),
#                 company_name_for_emails=entry_data.get('company_name_for_emails', ''),
#                 email=entry_data.get("email", ''),
#                 email_status=entry_data.get("email_status", ''),
#                 email_confidence=entry_data.get("email_confidence", ''),
#                 primary_email_catch_allstatus=entry_data.get("primary_email_catch_allstatus", ''),
#                 primary_email_last_verified_at=entry_data.get("primary_email_last_verified_at", ''),
#                 seniority=entry_data.get("seniority", ''),
#                 department=entry_data.get("department", ''),
#                 contact_owner=entry_data.get("contact_owner", ''),
#                 first_phone=entry_data.get("first_phone", ''),
#                 work_direct_phone=entry_data.get("work_direct_phone", ''),
#                 home_phone=entry_data.get("home_phone", ''),
#                 mobile_phone=entry_data.get("mobile_phone", ''),
#                 corporate_phone=entry_data.get("corporate_phone", ''),
#                 other_phone=entry_data.get("other_phone", ''),
#                 stage=entry_data.get("stage", ''),
#                 lists=entry_data.get("lists", ''),
#                 last_contacted=entry_data.get("last_contacted", ''),
#                 account_owner=entry_data.get("account_owner", ''),
#                 employees=entry_data.get("employees", ''),
#                 industry=entry_data.get("industry", ''),
#                 keywords=entry_data.get("keywords", ''),
#                 person_linkedin_url=entry_data.get("person_linkedin_url", ''),
#                 website=entry_data.get("website", ''),
#                 company_linkedin_url=entry_data.get("company_linkedin_url", ''),
#                 facebook_url=entry_data.get("facebook_url", ''),
#                 twitter_url=entry_data.get("twitter_url", ''),
#                 city=entry_data.get("city", ''),
#                 state=entry_data.get("state", ''),
#                 country=entry_data.get("country", ''),
#                 company_address=entry_data.get("company_address", ''),
#                 company_city=entry_data.get("company_city", ''),
#                 company_state=entry_data.get("company_state", ''),
#                 company_country=entry_data.get("company_country", ''),
#                 company_phone=entry_data.get("company_phone", ''),
#                 seo_description=entry_data.get("seo_description", ''),
#                 technologies=entry_data.get("technologies", ''),
#                 annual_revenue=entry_data.get("annual_revenue", ''),
#                 total_funding=entry_data.get("total_funding", ''),
#                 latest_funding=entry_data.get("latest_funding", ''),
#                 latest_funding_amount=entry_data.get("latest_funding_amount", ''),
#                 last_raised_at=entry_data.get("last_raised_at", ''),
#                 email_sent=entry_data.get("email_sent", ''),
#                 email_open=entry_data.get("email_open", ''),
#                 email_bounced=entry_data.get("email_bounced", ''),
#                 replied=entry_data.get("replied", ''),
#                 demoed=entry_data.get("demoed", ''),
#                 number_of_retailed_locations=entry_data.get("number_of_retailed_locations", ''),
#                 apollo_contact_id=entry_data.get("apollo_contact_id", ''),
#                 apollo_account_id=entry_data.get("apollo_account_id", ''),
#                 primary_email_source=entry_data.get("primary_email_source", ''),
#                 secondary_email=entry_data.get("secondary_email", ''),
#                 secondary_email_source=entry_data.get("secondary_email_source"),
#                 tertiary_email=entry_data.get("tertiary_email", ''),
#                 tertiary_email_source=entry_data.get("tertiary_email_source"),
#                 primary_intent_topic=entry_data.get("primary", ''),
#                 primary_intent_score=entry_data.get("score", ''),
#                 secondary_intent_topic=entry_data.get("secondary_intent_topic", ''),
#                 secondary_intent_score=entry_data.get("secondary_intent_score", ''),
#                 created_at=entry_data["created_at"],
#                 updated_at=entry_data["updated_at"]
#             )
#             entries.append(entry)
#         return super().create(validated_data)


class CsvImportHistorySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = CsvImportHistroy
        extra_kwargs = {
                        'total_records': {'required': False},
                        'uploaded_by': {'required': False},
                        'created_by': {'required': False}
                       }
        fields = [
                  "username", 'total_records', 
                  'uploaded_by', 'created_by'
                 ]
    
    def get_username(self, obj):
        return obj.uploaded_by.first_name


class CsvExportHistorySerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    class Meta:
        model = CsvExportHistory
        extra_kwargs = {
                        'total_records': {'required': False},
                        'created_by': {'required': False},
                        'exported_by': {'required': False}
                        }
        fields = [
                  'username', 'total_records', 
                  'created_by', 'exported_by' 
                 ]
        
    def get_username(self, obj):
        return obj.created_by.first_name   