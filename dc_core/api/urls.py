from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_stock_data

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('market-data/', get_stock_data, name='market-data'),
] 