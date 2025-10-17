# apps/complexes/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'buildings', views.BuildingViewSet)
router.register(r'units', views.UnitViewSet)
router.register(r'parkings', views.ParkingViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'contracts', views.ContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('unit/<int:unit_id>/transfer-history/', views.unit_transfer_history),
    path('unit/<int:unit_id>/change-ownership/', views.change_unit_ownership),
    path('unit/<int:unit_id>/change-residency/', views.change_unit_residency),
]