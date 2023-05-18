from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *




urlpatterns = [
    path("", index),
    path("scrape/<int:store_id>", scrape_store),
    path("button/<int:store_id>/<slug:action>", button_action),
    path("product", product_list),
    path("scrap-data", scrap_data),
    path("cron-scrap-data", cron_scrap_data),
    path("listing-cron-scrap-data", listing_cron_scrap_data),
    path("api", TableData.as_view()),
    path("api/data", AllTableData.as_view()),
    path("api/request_data", TestDatatableAPIView.as_view()),
    path("api/test_csv", TestCsvExport.as_view()),    
    # path("delete", delete_all),    
]
