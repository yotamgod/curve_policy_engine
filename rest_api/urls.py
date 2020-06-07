from django.urls import path, include
from rest_framework import routers
from rest_api import views

app_name = 'rest_api'

router = routers.DefaultRouter()
router.register(r'policy_rule', views.PolicyRuleViewSet)
router.register(r'transactions', views.TransactionViewSet, basename='transactions')

urlpatterns = [
    path('', include(router.urls))
]