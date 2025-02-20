from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.financial_data import FinancialDataViewSet

router = DefaultRouter()
router.register(r'financial', FinancialDataViewSet, basename='financial')

urlpatterns = [
    path('', include(router.urls)),
] 