import itertools
import requests
from io import TextIOWrapper
from django.core.paginator import Paginator
from django.utils.encoding import smart_str
from django.forms.models import model_to_dict
from django.db import IntegrityError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Q
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.datasystem.task import process_databatch
from apps.datasystem.models import (
                                    DataEntry, 
                                    SavedData, 
                                    UserDataPurchase, 
                                    SavedList,
                                    CsvImportHistroy,
                                    CsvExportHistory
                                    )
from apps.datasystem.serializers import (
                                         BulkDataEntrySerializer, 
                                         DataEntrySerializer,
                                         DataSavedSerializer,
                                         DataSavedListSerializer,
                                         AllCompanyInfoSerializer,
                                         AllListSerializer,
                                         CsvImportHistorySerializer,
                                         CsvExportHistorySerializer
                                         )
from apps.datasystem.pagination import DataSystemPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from .filters import DataEntryFilter, SavedDataFilter
import csv
import logging

logger = logging.getLogger(__name__)


class GetCompanyInfoView(generics.ListAPIView):
    queryset = DataEntry.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = AllCompanyInfoSerializer

    def get(self, request, *args, **kwargs):
        company_names = DataEntry.objects.values_list('company', flat=True).distinct()
        jobtitle = list(DataEntry.objects.values_list('title', flat=True).distinct())
        city = DataEntry.objects.values_list('city', flat=True).distinct()
        state = DataEntry.objects.values_list('state', flat=True).distinct()
        country = DataEntry.objects.values_list('country', flat=True).distinct()
        keyword = DataEntry.objects.values_list('keywords', flat=True)
        technologies = DataEntry.objects.values_list('technologies', flat=True)
        country_names = list(country)
        city_names = list(city)
        state_names = list(state)

        while("" in country_names):
            country_names.remove("")
        while("" in city_names):
            city_names.remove("")
        while("" in state_names):
            state_names.remove("")

        while("" in jobtitle):
            jobtitle.remove("")
        # print(country_names)
        return Response({
                         "company": list(company_names),
                         "city": city_names,
                         "state": state_names,
                         "country": country_names,
                         "jobtitle": jobtitle,
                         "keyword": set(list(itertools.chain(*keyword))),
                         "technologies": set(list(itertools.chain(*technologies)))
                         }, status=status.HTTP_200_OK)


@receiver([post_save, post_delete], sender=SavedData)
class GetDataView(generics.ListAPIView):
    queryset = DataEntry.objects.all()
    serializer_class = DataEntrySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    pagination_class = DataSystemPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = DataEntryFilter
    ordering_fields = ['created_at']
    search_fields = [ 
                      "email_status", "company", "employees", "city", "state", 
                      "country", "industry", "keywords", "technologies",
                      "annual_revenue", "title"
                     ] 

    def get_serializer_context(self):
        # Ensure request user is passed in the context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get(self, request, *args, **kwargs):
        list_exclude = request.GET.get("list_exclude", '').split(',')
        list_count = 0
        if list_exclude:
            excluded_data_ids = (
                SavedList.objects.filter(folder_name__in=list_exclude)
                .values_list('data', flat=True)
                .distinct()
            )
            list_count = excluded_data_ids.count()
        
        # print(excluded_data_ids.count())

        # print("list count", list_count)
        saved_data = SavedData.objects.filter(user=request.user).count()
        total_data = DataEntry.objects.all().count()

        if list_count:
            # print("bitore")
            save_count = saved_data - list_count
        else:    
            save_count = saved_data

        net_new = total_data - saved_data
        response = super().get(request, *args, **kwargs)
        return Response({
            "data": response.data,
            "saved": save_count,
            "net_new": net_new
        }, status=status.HTTP_200_OK)


class UploadJsonBatchView(views.APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            serializer = BulkDataEntrySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DataEntryDeleteView(views.APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def delete(self, request):
        data_ids = request.data.get("data_ids")
        page = request.query_params.get("page")
        per_page = request.query_params.get("per_page", 10)
        if data_ids:
            DataEntry.objects.filter(peolloid__in=data_ids).delete()
            return Response({"message": "Data successfully deleted"}, 
                            status=status.HTTP_204_NO_CONTENT)
        elif page:
            # Delete data for the current page
            all_entries = DataEntry.objects.all()
            paginator = Paginator(all_entries, per_page)
            try:
                page_entries = paginator.page(page).object_list
                deleted_ids = list(page_entries.values_list("peolloid", flat=True))
                deleted_count, _ = DataEntry.objects.filter(peolloid__in=deleted_ids).delete()
                return Response(
                    {"message": f"{deleted_count} entries successfully deleted from page {page}"},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    

class DataEntryDetailView(generics.RetrieveDestroyAPIView):
    queryset = DataEntry.objects.all()
    serializer_class = DataEntrySerializer
    authentication_classes = [JWTAuthentication]

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return Response({"Delete": "Data Successfully Deleted"}, status=status.HTTP_200_OK)


class GetAllSavedData(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    queryset = SavedData.objects.all()
    serializer_class = DataSavedSerializer
    pagination_class = DataSystemPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SavedDataFilter
    ordering_fields = ['saved_at']
    search_fields = [
                      "data__email_status", "data__company", 
                      "data__employees", "data__city", 
                      "data__state", "data__country", "data__industry", 
                      "data__keywords", "data__technologies",
                      "data__annual_revenue", "data__title"
                    ]

    def get_queryset(self):
        return SavedData.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # print(queryset)
        page = self.paginate_queryset(queryset)
        total_data = DataEntry.objects.all().count()
        saved_data = SavedData.objects.filter(user=request.user).count()

        net_new = total_data - saved_data

        if page is not None:
            # print("page logic er modde")
            serializer = self.get_serializer(page, many=True)
            # print(serializer.data)
            return self.get_paginated_response({"data": serializer.data, 
                                                "total": total_data,
                                                "net_new": net_new
                                                })
        
        serializer = self.serializer_class(queryset, many=True)
        # print("baire", serializer.data)
        return Response({"data": serializer.data, 
                         "total": total_data,
                         "net_new": net_new
                         },
                        status=status.HTTP_200_OK
                        )
    

class GetAllSavedListData(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    queryset = SavedList.objects.all()
    serializer_class = DataSavedListSerializer
    pagination_class = DataSystemPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SavedDataFilter
    search_fields = [
                      "data__email_status", "data__company", "data__employees", 
                      "data__city", "data__state", "data__country", 
                      "data__industry", "data__keywords", "data__technologies", 
                      "data__annual_revenue", "data__title"
                    ]

    def get_queryset(self): 
        return SavedList.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # print(queryset)
        page = self.paginate_queryset(queryset)
        
        total_data = DataEntry.objects.all().count() 
        saved_data = SavedData.objects.filter(user=request.user).count()
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # print("serializer data", serializer.data)
            return self.get_paginated_response({"data": serializer.data, 
                                                "total": total_data,
                                                "saved": saved_data
                                                })
        
        return Response({
                         "data": serializer.data,
                         "total": total_data,
                         "saved": saved_data
                        },
                        status=status.HTTP_200_OK
                        )


class DataPurchaseView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        user = request.user
        data_ids = request.data.get("data_ids", [])
        url = request.data.get("url", "")
        page = request.data.get("page")
        page_size = request.data.get("page_size")
        all = request.data.get("all")
        new = request.data.get("new")
        current_page = request.data.get("currentpage")

        token = request.META.get("HTTP_AUTHORIZATION")

        headers = {
            "Authorization": token
        }

        if url:
            try:
                queryset = requests.get(url, headers=headers)
                queryset.raise_for_status()
                data_response = queryset.json()
                # print(data_response)
            except requests.RequestException as e:
                return Response({"error": f"Failed to fetch data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if all:
            alldata = []
            total_pages = data_response.get("total_page_number")

            # print("total--->", total_pages)

            for p in range(1, total_pages+1):
                paginated_url = f"{url}&page={p}&page_size={page_size}"
                response = requests.get(paginated_url, headers=headers)

                if response.status_code == 200:
                    if new:
                        page_data = response.json().get("results", {}).get("data", {})
                        # print("new er pagedata", page_data)
                    else:
                        page_data = response.json().get("data").get("results", {})
                        # print("total er pagedata", page_data)
                    alldata.extend(page_data)
                    # print("pagedata--->", page_data)
        
        elif current_page:
            alldata = []
            paginated_url = f"{url}&page={page}&page_size={page_size}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                if new:
                    page_data = response.json().get("results", {}).get("data", {})
                    # print("new er pagedata", page_data)
                else:
                    page_data = response.json().get("data").get("results", [])
                    # print("total er pagedata", page_data)
                alldata.extend(page_data)
        elif data_ids is not None:
            # print("data ids", data_ids)
            data = DataEntry.objects.filter(peolloid__in=data_ids)
            # print("data--->", data)
            alldata = [
                {
                    field: value
                    for field, value in model_to_dict(d).items()
                    if field != "user" and field != "created_at"
                }
                for d in data
            ]
            # print("alldata", alldata)



        # print("user and data ids", user, data_ids)
        # if not data_ids:
        #     return Response({'message': 'No data_ids provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
        to_be_purchased = []
        
        for data in alldata:
            try:
                data_id = data["peolloid"]
                # print("data--?", data_id)
                data_entry = DataEntry.objects.get(peolloid=data_id)
                # print("loop er modde")
                user_purchase, created = UserDataPurchase.objects.get_or_create(user=user, data=data_entry)

                if not user_purchase.is_purchased:
                    user_purchase.is_purchased = True
                    user_purchase.save()
                    SavedData.objects.get_or_create(
                        user=user,
                        data=data_entry
                    )
                    # print(data_id)
                    to_be_purchased.append(data_id)
                    # print(f"data id -> {data_id} added to the array")
            except DataEntry.DoesNotExist:
                continue
           
        total_credit = 1.00 * len(to_be_purchased)
        # print(user.credit, total_credit, len(to_be_purchased))
        if user.credit >= total_credit:
            user.credit -= total_credit
            user.save()
            return Response({"message": "Successfully purchased data."}, status=status.HTTP_200_OK)
        else:
            UserDataPurchase.objects.filter(user=user, data__in=to_be_purchased).delete()
            UserDataPurchase.objects.filter(user=user, data__in=to_be_purchased).update(is_purchased=False)
            SavedData.objects.filter(user=user, data__in=to_be_purchased).delete()
            return Response({"message": "Your have not suffiecient credits"}, status=status.HTTP_403_FORBIDDEN)

        # return Response(status=status.HTTP_200_OK)


class DataDownloadView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        # folder_name = request.data.get('folder_name')
        data_ids = request.data.get('data_ids', [])
        url = request.data.get("url", "")
        page = request.data.get("page")
        page_size = request.data.get("page_size")
        select = request.data.get("select")
        limit = request.data.get("limit")
        all = request.data.get("all")
        current_page = request.data.get("currentpage")
        # print(current_page)
        
        token = request.META.get("HTTP_AUTHORIZATION")
        # print(token)
        headers = {
            'Authorization': token,
        }
        
        if url:
            try:
                # print("url try er modde")
                queryset = requests.get(url, headers=headers, verify=False)
                queryset.raise_for_status()
                data_response = queryset.json()
                # print(data_response)
            except requests.exceptions.RequestException as e:
                return Response({"error": f"Failed to fetch data: {str(e)}"}, 
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        if all:
            # print(data_response)
            # print("all er modde")
            alldata = []
            total_pages = data_response.get("total_page_number") 

            for p in range(1, total_pages+1):
                paginated_url = f"{url}&page={p}&page_size={page_size}"
                response = requests.get(paginated_url, headers=headers)

                if response.status_code == 200:
                    # print("success")
                    page_data = response.json().get("results", {}).get("data", [])
                    alldata.extend(page_data)
        
        elif current_page:
            # print("else er modde---->")
            alldata = []
            paginated_url = f"{url}&page={page}&page_size={page_size}"
            response = requests.get(paginated_url, headers=headers)
            if response.status_code == 200:
                # print("success")
                page_data = response.json().get("results", {}).get("data", [])
                alldata.extend(page_data)

        elif select:
            # print("select er modde")
            alldata = []
            total_pages = data_response.get("total_page_number") 
   
            for p in range(1, total_pages+1):
                paginated_url = f"{url}&page={p}&page_size={page_size}"
                response = requests.get(paginated_url, headers=headers)

                if response.status_code == 200:
                    # print("success")
                    page_data = response.json().get("results", {}).get("data", [])
                    alldata.extend(page_data)
        
        # if limit is not None:
        #     try:
        #         limit = int(limit)
        #         alldata = alldata[:limit]
        #     except ValueError:
        #         return Response({"error": "Invalid limit value"}, status=status.HTTP_400_BAD_REQUEST)

        elif data_ids is not None:
            data = SavedData.objects.filter(user=user, data__peolloid__in=data_ids)
            alldata = [
                {
                    "data": {
                        field: value
                        for field, value in model_to_dict(d.data).items()
                        if field != "user" and field != "created_at"
                    }
                }
                for d in data
            ]
        
        # elif select:
        #     alldata = []
        #     total_pages = data_response.get("total_page_number") 
   
        #     for p in range(1, total_pages+1):
        #         paginated_url = f"{url}&page={p}&page_size={page_size}"
        #         response = requests.get(paginated_url, headers=headers)
        #         print("alldata", response)
        #         if response.status_code == 200:
        #             # print("success")
        #             page_data = response.json().get("results", {}).get("data", [])
        #             alldata.extend(page_data)
        
        if limit is not None:
            try:
                limit = int(limit)
                alldata = alldata[:limit]
            except ValueError:
                return Response({"error": "Invalid limit value"}, status=status.HTTP_400_BAD_REQUEST)
        

        # item_ids = []
        # for data in alldata:
        #     data = data["data"]
        #     print(data["peolloid"])
        #     item_ids.append(data["peolloid"])
        

        # data = SavedData.objects.filter(user=user, data__peolloid__in=item_ids)

        


        # if not data_ids:
        #     return Response({'error': 'No data IDs provided for download.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # to_be_purchased = []

        # Export_History = CsvExportHistory.objects.create(
        #     type=folder_name,
        #     total_records=len(data_ids),
        #     created_by=request.user
        # )
        
        # for data_id in data_ids:
        #     try:
        #         data_entry = DataEntry.objects.get(peolloid=data_id)
        #         user_purchase, created = UserDataPurchase.objects.get_or_create(user=user, data=data_entry)
                
        #         if not user_purchase.is_purchased:
        #             user_purchase.is_purchased = True
        #             user_purchase.save()
        #             SavedData.objects.get_or_create(
        #                 user=user,
        #                 data=data_entry
        #             )
        #             to_be_purchased.append(data_id)
        #     except data_entry.DoesNotExist:
        #         continue
            
        # total_credit = 0.001 * len(to_be_purchased)
        # if user.credit > total_credit:
        #     user.credit -= total_credit
        #     user.save()
            # Export_History.credits = total_credit
            # Export_History.save()
        # else:
            # UserDataPurchase.objects.filter(data__peolloid__in=data_ids).delete()
            # UserDataPurchase.objects.filter(data__peolloid__in=data_ids).update(is_purchased=False)
            # return Response({"message": "Insufficient credits"}, status=status.HTTP_403_FORBIDDEN)
        
        # purchase_entries = UserDataPurchase.objects.filter(user=user, data__peolloid__in=data_ids)

        # if not purchase_entries.exists():
        #     return Response({'error': 'No purchased data found for the specified folder.'}, status=status.HTTP_404_NOT_FOUND)
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f"attachment; filename='peollo.csv'"

        # Wrap the response object with a writer that can handle Unicode
        writer = csv.writer(TextIOWrapper(response, encoding='utf-8-sig'), quoting=csv.QUOTE_MINIMAL)

        writer = csv.writer(response)
        writer.writerow([
                         'ID', 'First Name', 'Last Name', 'Title', 
                         'Company', 'Company Name For Emails', 'Email',
                         'Email Status', 'Email Confidence', 
                         'Primary Email Catch Allstatus',
                         'Primary Email Last Verified_at',
                         "Seniority", "Department", 
                         "Contact Owner", "First Phone", "Work Direct Phone", 
                         "Home Phone", "Mobile Phone", "Corporate Phone",
                         "Other Phone", "Stage", "Lists", "Last Contacted", 
                         "Account Owner", "Employees", "Industry", "Keywords", 
                         "Person Linkedin url", "Website", "Company Linkedin Url",
                         "Facebook Url", "Twitter Url", "City", "State", "Country", 
                         "Company Address", "Company City", "Company State", 
                         "Company Country", "company_phone", "Seo Description", "Technologies",
                         "Annual Revenue", "Total Funding", "Latest Funding", 
                         "Latest Funding Amount", "Last Raised_at", "Email Sent", 
                         "Email Open", "Email Bounced", "Replied", "Demoed",
                         "Number Of Retailed Locations", "Apollo Contact Id",
                         "Apollo Account Id", "Primary Email Source", 
                         "Secondary Email", "Secondary Email Source",
                         "Tertiary Email", "Tertiary Email Source", 
                         "Primary Intent Topic", "Primary Intent Score", 
                         "Secondary Intent Topic", "Secondary Intent Score",
                        ])
        
        for item in alldata:
            data = item.get("data", {})
            writer.writerow([
                smart_str(data["peolloid"]),
                smart_str(data["first_name"]),
                smart_str(data["last_name"]),
                smart_str(data["title"]),
                smart_str(data["company"]),
                smart_str(data["company_name_for_emails"]),
                smart_str(data["email"]),
                smart_str(data["email_status"]),
                smart_str(data["email_confidence"]),
                smart_str(data["primary_email_catch_allstatus"]),
                smart_str(data["primary_email_last_verified_at"]),
                smart_str(data["seniority"]),
                smart_str(data["department"]),
                smart_str(data["contact_owner"]),
                smart_str(data["first_phone"]),
                smart_str(data["work_direct_phone"]),
                smart_str(data["home_phone"]),
                smart_str(data["mobile_phone"]),
                smart_str(data["corporate_phone"]),
                smart_str(data["other_phone"]),
                smart_str(data["stage"]),
                smart_str(data["lists"]),
                smart_str(data["last_contacted"]),
                smart_str(data["account_owner"]),
                smart_str(data["employees"]),
                smart_str(data["industry"]),
                smart_str(data["keywords"]),
                smart_str(data["person_linkedin_url"]),
                smart_str(data["website"]),
                smart_str(data["company_linkedin_url"]),
                smart_str(data["facebook_url"]),
                smart_str(data["twitter_url"]),
                smart_str(data["city"]),
                smart_str(data["state"]),
                smart_str(data["country"]),
                smart_str(data["company_address"]),
                smart_str(data["company_city"]),
                smart_str(data["company_state"]),
                smart_str(data["company_country"]),
                smart_str(data["company_phone"]),
                smart_str(data["seo_description"]),
                smart_str(data["technologies"]),
                smart_str(data["annual_revenue"]),
                smart_str(data["total_funding"]),
                smart_str(data["latest_funding"]),
                smart_str(data["last_raised_at"]),
                smart_str(data["email_sent"]),
                smart_str(data["email_open"]),
                smart_str(data["email_bounced"]),
                smart_str(data["replied"]),
                smart_str(data["demoed"]),
                smart_str(data["number_of_retailed_locations"]),
                smart_str(data["apollo_account_id"]),
                smart_str(data["apollo_contact_id"]),
                smart_str(data["primary_email_source"]),
                smart_str(data["secondary_email"]),
                smart_str(data["secondary_email_source"]),
                smart_str(data["tertiary_email"]),
                smart_str(data["tertiary_email_source"]),
                smart_str(data["primary_intent_topic"]), 
                smart_str(data["primary_intent_score"]),
                smart_str(data["secondary_intent_topic"]),
                smart_str(data["secondary_intent_score"])
            ])
        
        CsvExportHistory.objects.create(
                    total_records=len(alldata),
                    created_by=user
                )

        # for purchase_data in purchase_entries:
        #     data_entry = purchase_data.data
        #     writer.writerow([
        #           data_entry.peolloid,
        #           data_entry.first_name,
        #           data_entry.last_name,
        #           data_entry.title,
        #           data_entry.company,
        #           data_entry.company_name_for_emails,
        #           data_entry.email,
        #           data_entry.email_status,
        #           data_entry.email_confidence,
        #           data_entry.primary_email_catch_allstatus,
        #           data_entry.primary_email_last_verified_at,
        #           data_entry.seniority,
        #           data_entry.department,
        #           data_entry.contact_owner,
        #           data_entry.first_phone,
        #           data_entry.work_direct_phone,
        #           data_entry.home_phone,
        #           data_entry.mobile_phone,
        #           data_entry.corporate_phone,
        #           data_entry.other_phone,
        #           data_entry.stage,
        #           data_entry.lists,
        #           data_entry.last_contacted,
        #           data_entry.account_owner,
        #           data_entry.employees,
        #           data_entry.industry,
        #           data_entry.keywords,
        #           data_entry.person_linkedin_url,
        #           data_entry.website,
        #           data_entry.company_linkedin_url,
        #           data_entry.facebook_url,
        #           data_entry.twitter_url,
        #           data_entry.city,
        #           data_entry.state,
        #           data_entry.country,
        #           data_entry.company_address,
        #           data_entry.company_city,
        #           data_entry.company_state,
        #           data_entry.company_country,
        #           data_entry.seo_description,
        #           data_entry.technologies,
        #           data_entry.annual_revenue,
        #           data_entry.total_funding,
        #           data_entry.latest_funding,
        #           data_entry.last_raised_at,
        #           data_entry.email_sent,
        #           data_entry.email_open,
        #           data_entry.email_bounced,
        #           data_entry.replied,
        #           data_entry.demoed,
        #           data_entry.number_of_retailed_locations,
        #           data_entry.apollo_account_id,
        #           data_entry.apollo_contact_id,
        #           data_entry.primary_email_source,
        #           data_entry.secondary_email,
        #           data_entry.secondary_email_source,
        #           data_entry.tertiary_email,
        #           data_entry.tertiary_email_source,
        #           data_entry.primary_intent_topic, 
        #           data_entry.primary_intent_score,
        #           data_entry.secondary_intent_topic,
        #           data_entry.secondary_intent_score
        #     ]) 

        return response
        

class SavedListViews(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        data_ids = request.data.get('data_ids', [])
        url = request.data.get("url", "")
        page = request.data.get("page")
        page_size = request.data.get("page_size")
        all = request.data.get("all")
        new = request.data.get("new")
        saved = request.data.get("saved")
        select = request.data.get("select")
        limit = request.data.get("limit")
        current_page = request.data.get("currentpage")
        folder_name = request.data.get('folder_name')
        exported_count = 0
        # folder_name = folder_name[0]
        # print("Folder_name--->",folder_name)
        
        # print("page", url)

        token = request.META.get("HTTP_AUTHORIZATION")
        headers = {
            "Authorization": token
        }
        # print("token", token)

        if url:
            try:
                queryset = requests.get(url, headers=headers)
                queryset.raise_for_status()
                data_response = queryset.json()
                
            except requests.RequestException as e:
                return Response({"error": f"Failed to fetch data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # if not data_ids:
        #     return Response({"message": "No data ids provided for Saved in the list"}, status=status.HTTP_400_BAD_REQUEST)
        
        if all:
            alldata = []
            if new or saved:
                total_pages = data_response.get("total_page_number")
            else:
                total_pages = data_response.get("data").get("total_page_number")

            # print("total--->", total_pages)

            for p in range(1, total_pages+1):
                paginated_url = f"{url}&page={p}&page_size={page_size}"
                response = requests.get(paginated_url, headers=headers)
                # print("res", response)
                if response.status_code == 200:
                    if new:
                        page_data = response.json().get("results", {}).get("data", {})
                        # print("new er pagedata", page_data)
                    elif saved:
                        page_data = [
                                    item.get("data") 
                                    for item in response.json().get("results", {}).get("data", [])
                                ]
                    else:
                        page_data = response.json().get("data").get("results", {})
                        # print("total er pagedata", page_data)
                    alldata.extend(page_data)
        
        elif current_page:
            alldata = []
            paginated_url = f"{url}&page={page}&page_size={page_size}"

            response = requests.get(paginated_url, headers=headers)
            # print("response object", response.json())
            if response.status_code == 200:
                if new:
                    page_data = response.json().get("results", {}).get("data", {})
                    # print("new er pagedata", page_data)
                elif saved:
                    page_data = [
                                    item.get("data") 
                                    for item in response.json().get("results", {}).get("data", [])
                                ]
                    # print("page", page_data)
                else:
                    page_data = response.json().get("data").get("results", {})
                    # print("total er pagedata", page_data)
                alldata.extend(page_data)
        
        elif select:
            # print("select er modde")
            alldata = []
            if new or saved:
                total_pages = data_response.get("total_page_number")
            else:
                total_pages = data_response.get("data").get("total_page_number")

            # print("total--->", total_pages)

            for p in range(1, total_pages+1):
                paginated_url = f"{url}&page={p}&page_size={page_size}"
                response = requests.get(paginated_url, headers=headers)
                # print("res", response)
                if response.status_code == 200:
                    if new:
                        page_data = response.json().get("results", {}).get("data", {})
                        # print("new er pagedata", page_data)
                    elif saved:
                        page_data = [
                                    item.get("data") 
                                    for item in response.json().get("results", {}).get("data", [])
                                ]
                    else:
                        page_data = response.json().get("data").get("results", {})
                        # print("total er pagedata", page_data)
                    alldata.extend(page_data)
    
        elif data_ids is not None:
            # print("data ids", data_ids)
            data = DataEntry.objects.filter(peolloid__in=data_ids)
            # print("data--->", data)
            alldata = [
                {
                    field: value
                    for field, value in model_to_dict(d).items()
                    if field != "user" and field != "created_at"
                }
                for d in data
            ]
         
        if limit is not None:
            try:
                limit = int(limit)
                alldata = alldata[:limit]
            except ValueError:
                return Response({"error": "Invalid limit value"}, status=status.HTTP_400_BAD_REQUEST)
            


        unpurchase = []
         
        for data in alldata:
            try:
                data_id = data.get("peolloid")
                # print(type(data_id))
                saveddata = SavedData.objects.get(user=user, data__peolloid=data_id)
                # print("peolloid", saveddata.data.peolloid)
                data_entry = DataEntry.objects.get(peolloid=saveddata.data.peolloid)
                # print("dataentry-->", data_entry)
                SavedList.objects.get_or_create(user=user, folder_name=folder_name, data=data_entry)
            except SavedData.DoesNotExist:
                unpurchase.append(data_id)
                # print(data_id)
                continue
        # print(unpurchase)
        if unpurchase is not None:
            for data_id in unpurchase:
                try:
                    data = DataEntry.objects.get(peolloid=data_id)
                    # print("unpurchase data", data)
                    # print("loop er modde")
                    user_purchase, created = UserDataPurchase.objects.get_or_create(user=user, data=data)

                    if not user_purchase.is_purchased:
                        user_purchase.is_purchased = True
                        user_purchase.save()
                        SavedData.objects.get_or_create(
                            user=user,
                            data=data
                        )
                        SavedList.objects.get_or_create(user=user, folder_name=folder_name, data=data)
                        
                        # print(f"data id -> {data_id} added to the array")
                except Exception as e:
                    continue
            
        #     # print(unpurchase)

            total_credit = 1 * len(unpurchase)
            # print(user.credit, total_credit, len(unpurchase))
            if user.credit >= total_credit:
                user.credit -= total_credit
                user.save()
                return Response({"message": "Successfully Saved data & added to the list"}, status=status.HTTP_200_OK)
            else:
                UserDataPurchase.objects.filter(user=user, data__in=unpurchase).delete()
                UserDataPurchase.objects.filter(user=user, data__in=unpurchase).update(is_purchased=False)
                SavedData.objects.filter(user=user, data__in=unpurchase).delete()
                SavedList.objects.filter(user=user, data__in=unpurchase).delete()
                return Response({"message": "Your have not suffiecient credits"}, status=status.HTTP_403_FORBIDDEN) 
        
        return Response({"message": "Data Successfully Added to the save list"})


class NetNewData(views.APIView):
    serializer_class = DataEntrySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    # filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter] 
    pagination_class = DataSystemPagination
    # filterset_class = DataEntryFilter
    search_fields = [
                      "email_status"
                    ]

    def get_serializer_context(self):
        # Ensure request user is passed in the context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get(self, request):
        purchase_data = UserDataPurchase.objects.filter(
            user=request.user, is_purchased=True
        ).values_list("data__peolloid", flat=True)
        new_data = DataEntry.objects.exclude(peolloid__in=purchase_data)

        # Apply filters manually
        filter_backend = DjangoFilterBackend()
        filterset = DataEntryFilter(request.GET, queryset=new_data, request=request)
        if filterset.is_valid():
            new_data = filterset.qs

        paginator = self.pagination_class()
        paginated_new_data = paginator.paginate_queryset(new_data, request)
        saved_data = SavedData.objects.filter(user=request.user).count()
        total_data = DataEntry.objects.all().count()

        if paginated_new_data is not None:
            serializer = self.serializer_class(paginated_new_data, many=True)
            return paginator.get_paginated_response({
                "data": serializer.data,
                "total": total_data,
                "saved": saved_data,
            })

        serializer = self.serializer_class(new_data, many=True)
        return Response({
            "data": serializer.data,
            "total": total_data,
            "saved": saved_data,
        }, status=status.HTTP_200_OK)


# Get All Foder Name
class AllFoderNameViews(generics.ListAPIView):
    queryset = SavedList.objects.all()
    serializer_class = AllListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]    

    def get_queryset(self): 
        return SavedList.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
          
        unique_names = {}

        for item in queryset:
            folder_name = item.folder_name
            # print(folder_name)
            if folder_name not in unique_names:
                unique_names[folder_name] = item
            
        unique_data = list(unique_names.values())
        
        page = self.paginate_queryset(unique_data)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response({"data": serializer.data, 
                                                })
        
        serializer = self.serializer_class(unique_data, many=True)
        return Response({
                         "data": serializer.data,
                        },
                        status=status.HTTP_200_OK
                        )
    

# should be make it distinct value 
class ListFolderUpdateDeleteViews(generics.RetrieveUpdateDestroyAPIView):
    queryset = SavedList.objects.all()
    serializer_class = DataSavedListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]        
    
    def delete(self, request, folder_name):
        has = SavedList.objects.filter(folder_name=folder_name, user=request.user).delete()
        
        if has is not None:
            return Response({"message": "Saved List Data Successfully Deleted"},
                            status=status.HTTP_204_NO_CONTENT
                            )
        else:
            return Response({"message": "List not found in this name"},
                            status=status.HTTP_404_NOT_FOUND
                            )
    
    def partial_update(self, request, folder_name):
        folder = SavedList.objects.filter(folder_name=folder_name, user=request.user)

        if folder.exists():
            new_folder_name = request.data.get("folder_name")
            # print(new_folder_name)
            has = folder.update(folder_name=new_folder_name)

        if has is not None:
            return Response({"message": "Folder Name Sucessfully updated"},
                            status=status.HTTP_200_OK
                            )
        else:
            return Response({"message": "No List found in this name"},
                            status=status.HTTP_404_NOT_FOUND
                            )


class CvImportHistoryViews(generics.ListAPIView):
    queryset = CsvImportHistroy.objects.all()
    serializer_class = CsvImportHistorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)
    #     # return Response(response.data, status=status.HTTP_200_OK)
    

class CvExportHistoryViews(generics.ListAPIView):
    queryset = CsvExportHistory.objects.all()
    serializer_class = CsvExportHistorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)
        # return Response(response.data, status=status.HTTP_200_OK)