from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'charge-templates', views.ChargeTemplateViewSet)
router.register(r'charges', views.ChargeViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'invoices', views.InvoiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]