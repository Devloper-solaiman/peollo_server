from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DataSystemPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    
    def get_paginated_response(self, data):
        return Response({
            'total_data_count': self.page.paginator.count,
            'total_page_number': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })