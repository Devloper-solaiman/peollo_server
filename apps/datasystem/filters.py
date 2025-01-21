from django_filters import rest_framework as filters
from django.db.models import Q
from apps.datasystem.models import DataEntry, SavedList


class CustomCharInFilter(filters.BaseInFilter, filters.CharFilter):
    def filter(self, qs, value):
        # print('filter function er modde', type(value))
        if value:
            if isinstance(value, list):
                value = ','.join(value)

            value_list = [v.strip() for v in value.split(',')]
            query = Q()
            for val in value_list:
                query |= Q(**{f"{self.field_name}__iexact": val})
            qs = qs.filter(query)
        return qs


class DataEntryFilter(filters.FilterSet):
    email_status = CustomCharInFilter(field_name='email_status')
    title = CustomCharInFilter(field_name='title')
    company = CustomCharInFilter(field_name='company')
    city = filters.CharFilter(method='filter_city_state_country')
    state = filters.CharFilter(method='filter_city_state_country')
    country = filters.CharFilter(method='filter_city_state_country')
    industry = CustomCharInFilter(field_name='industry')
    keywords = CustomCharInFilter(field_name='keywords')
    technologies = CustomCharInFilter(field_name='technologies')
    
    list_exclude = filters.CharFilter(method='list_filter_exclude')

    employees_min = filters.NumberFilter(field_name='employees', lookup_expr='gte')
    employees_max = filters.NumberFilter(field_name='employees', lookup_expr='lte')

    revenue_min = filters.NumberFilter(field_name='annual_revenue', lookup_expr='gte')
    revenue_max = filters.NumberFilter(field_name='annual_revenue', lookup_expr='lte')

    title_include = filters.CharFilter(method='filter_include_title')
    title_exclude = filters.CharFilter(method='filter_exclude_title')
    company_include = filters.CharFilter(method='filter_include_company')
    company_exclude = filters.CharFilter(method='filter_exclude_company')
    keywords_include = filters.CharFilter(method='filter_include_keywords')
    keywords_exclude = filters.CharFilter(method='filter_exclude_keywords')
    technologies_include = filters.CharFilter(method='filter_include_technologies')
    technologies_exclude = filters.CharFilter(method='filter_exclude_technologies')

    def filter_city_state_country(self, queryset, name, value):
        """
        Filters city, state, or country independently and combines the results.
        """
        city = self.data.get('city', None)
        state = self.data.get('state', None)
        country = self.data.get('country', None)

        query = Q()

        if city:
            # Handle multiple cities
            cities = [c.strip() for c in city.split(',')]
            city_query = Q()
            for c in cities:
                city_query |= Q(city__iexact=c)
            query |= city_query

        if state:
            # Handle multiple states
            states = [s.strip() for s in state.split(',')]
            state_query = Q()
            for s in states:
                state_query |= Q(state__iexact=s)
            query |= state_query

        if country:
            # Handle multiple countries
            countries = [c.strip() for c in country.split(',')]
            country_query = Q()
            for c in countries:
                country_query |= Q(country__iexact=c)
            query |= country_query

        if query:
            return queryset.filter(query)
        return queryset

    def filter_include_title(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'title', value)

    def filter_exclude_title(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'title', value)

    def filter_include_company(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'company', value)

    def filter_exclude_company(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'company', value)

    def filter_include_technologies(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'technologies', value)

    def filter_exclude_technologies(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'technologies', value)
    
    def filter_include_keywords(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'keywords', value)

    def filter_exclude_keywords(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'keywords', value)

    def apply_include_filter(self, queryset, field_name, value):
        if value:
            include_values = [v.strip() for v in value.split(',')]
            query = Q()
            for val in include_values:
                query |= Q(**{f"{field_name}__icontains": val})
            return queryset.filter(query)
        return queryset

    def apply_exclude_filter(self, queryset, field_name, value):
        if value:
            exclude_values = [v.strip() for v in value.split(',')]
            for val in exclude_values:
                queryset = queryset.exclude(**{f"{field_name}__icontains": val})
        return queryset
    
    # def filter_revenue_min(self, queryset, name, value):
    #     if value:
    #         query = Q()
    #         for entry in queryset:
    #             revenue_count = int(entry.annual_revenue)
    #             # print("revenue>>>", type(revenue_count), type(value))
    #             if revenue_count >= value:
    #                 query |= Q(peolloid=entry.peolloid)
    #         return queryset.filter(query)
    #     return queryset
    
    # def filter_revenue_max(self, queryset, name, value):
    #     if value:
    #         query = Q()
    #         for entry in queryset:
    #             revenue_count = int(entry.annual_revenue)
    #             if revenue_count <= value:
    #                 query |= Q(peolloid=entry.peolloid)
    #         return queryset.filter(query)
    #     return queryset
    
    def filter_min_employees(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(Q(employees__isnull=False) & Q(employees__gte=str(value)))
        return queryset

    def filter_max_employees(self, queryset, name, value):
        if value is not None:
            queryset = queryset.filter(Q(employees__isnull=False) & Q(employees__lte=str(value)))
        return queryset
    

    # def filter_min_employees(self, queryset, name, value):
    #     if value:
    #         queryset = queryset.filter(employees__gte=value)
    #     return queryset

    # def filter_max_employees(self, queryset, name, value):
    #     if value:
    #         queryset = queryset.filter(employees__lte=value)
    #     return queryset

    def list_filter_exclude(self, queryset, name, value):
        if value:
            
            exclude_data_ids = SavedList.objects.filter(folder_name__in=value.split(',')).values_list('data', flat=True)
            
            return queryset.exclude(peolloid__in=exclude_data_ids)
        return queryset


class SavedDataFilter(filters.FilterSet):
    email_status = CustomCharInFilter(field_name='data__email_status')
    industry = CustomCharInFilter(field_name='data__industry')
    city = filters.CharFilter(method='filter_city_state_country')
    state = filters.CharFilter(method='filter_city_state_country')
    country = filters.CharFilter(method='filter_city_state_country')
    folder_name = CustomCharInFilter(field_name='folder_name')
    list_exclude = CustomCharInFilter(method='list_filter_exclude')

    employees_min = filters.NumberFilter(field_name='data__employees', lookup_expr='gte')
    employees_max = filters.NumberFilter(field_name='data__employees', lookup_expr='lte')

    revenue_min = filters.NumberFilter(field_name='data__annual_revenue', lookup_expr='gte')
    revenue_max = filters.NumberFilter(field_name='data__annual_revenue', lookup_expr='lte')

    title_include = CustomCharInFilter(method='filter_include_title')
    title_exclude = CustomCharInFilter(method='filter_exclude_title')
    company_include = CustomCharInFilter(method='filter_include_company')
    company_exclude = CustomCharInFilter(method='filter_exclude_company')
    keywords_include = CustomCharInFilter(method='filter_include_keywords')
    keywords_exclude = CustomCharInFilter(method='filter_exclude_keywords')
    technologies_include = CustomCharInFilter(method='filter_include_technologies')
    technologies_exclude = CustomCharInFilter(method='filter_exclude_technologies')

    def filter_city_state_country(self, queryset, name, value):
        """
        Filters city, state, or country independently and combines the results.
        """
        city = self.data.get('city', None)
        state = self.data.get('state', None)
        country = self.data.get('country', None)
        
        query = Q()

        if city:
            # Handle multiple cities
            cities = [c.strip() for c in city.split(',')]
            city_query = Q()
            for c in cities:
                city_query |= Q(data__city__iexact=c)
            query |= city_query

        if state:
            # Handle multiple states
            states = [s.strip() for s in state.split(',')]
            state_query = Q()
            for s in states:
                state_query |= Q(data__state__iexact=s)
            query |= state_query

        if country:
            # Handle multiple countries
            countries = [c.strip() for c in country.split(',')]
            country_query = Q()
            for c in countries:
                country_query |= Q(data__country__iexact=c)
            query |= country_query

        if query:
            return queryset.filter(query)
        return queryset
    
    def list_filter_exclude(self, queryset, name, value):
        if value:
            exclude_data_ids= SavedList.objects.filter(folder_name__in=value).values_list('data', flat=True)
            # print(exclude_data_ids)
            return queryset.exclude(data__peolloid__in=exclude_data_ids)
        return queryset

    def filter_min_employees(self, queryset, name, value):
        if value:
            queryset = queryset.filter(data__employees__gte=value)
        return queryset

    def filter_max_employees(self, queryset, name, value):
        if value:
            queryset = queryset.filter(data__employees__lte=value)
        return queryset
    
    # def filter_revenue_min(self, queryset, name, value):
    #     if value:
    #         value = int(value[0])
    #         query = Q()
    #         for entry in queryset:
    #             revenue_count = int(entry.data.annual_revenue)
    #             # print("revenue>>>", entry.data.peolloid)
    #             if revenue_count >= value:
    #                 query |= Q(data__peolloid=entry.data.peolloid)
    #         return queryset.filter(query)
    #     return queryset

    # def filter_revenue_max(self, queryset, name, value):
    #     if value:
    #         value = int(value[0])
    #         query = Q()
    #         for entry in queryset:
    #             revenue_count = int(entry.data.annual_revenue)
    #             # print("rv->>>>", revenue_count)
    #             if revenue_count <= value:
    #                 query |= Q(data__peolloid=entry.data.peolloid)
    #         return queryset.filter(query)
    #     return queryset

    def filter_include_title(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'data__title', value)

    def filter_exclude_title(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'data__title', value)
    
    def filter_include_company(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'data__company', value)

    def filter_exclude_company(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'data__company', value)
    
    def filter_include_keywords(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'data__keywords', value)

    def filter_exclude_keywords(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'data__keywords', value)
    
    def filter_include_technologies(self, queryset, name, value):
        return self.apply_include_filter(queryset, 'data__technologies', value)

    def filter_exclude_technologies(self, queryset, name, value):
        return self.apply_exclude_filter(queryset, 'data__technologies', value)

    def apply_include_filter(self, queryset, field_name, value):
        if isinstance(value, list):
            value_list = value
        else:
            value_list = [v.strip() for v in value.split(',')]

        if value_list:
            query = Q()
            for val in value_list:
                query |= Q(**{f"{field_name}__icontains": val})
            return queryset.filter(query)
        return queryset
    
    def apply_exclude_filter(self, queryset, field_name, value):
        if isinstance(value, list):
            value_list = value
        else:
            value_list = [v.strip() for v in value.split(',')]
            print(value_list)

        if value_list:
            query = Q()
            for val in value_list:
                query |= Q(**{f"{field_name}__icontains": val})
            return queryset.exclude(query)
        return queryset
    

