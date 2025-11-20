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
    #path('', include(router.urls)),

    # Singular/nested endpoints to match API documentation
    # Building list & detail (singular path)
    path('building/', views.BuildingViewSet.as_view({'get': 'list', 'post': 'create'}), name='building-list'),
    path('building/<int:building_id>/', views.BuildingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='building-detail'),

    # Nested under building: units, parkings, warehouses
    path('building/<int:building_id>/unit/', views.BuildingViewSet.as_view({'get': 'units'}), name='building-units'),
    path('building/<int:building_id>/unit/<int:unit_id>/', views.unit_detail_in_building, name='building-unit-detail'),
    path('building/<int:building_id>/unit/<int:unit_id>/TransferHistory/', views.unit_transfer_history_in_building, name='building-unit-transfer-history'),
    path('building/<int:building_id>/unit/<int:unit_id>/TransferHistory/<int:history_id>/', views.unit_transfer_history_detail_in_building, name='building-unit-transfer-history-detail'),

    path('building/<int:building_id>/parking/', views.BuildingViewSet.as_view({'get': 'parkings'}), name='building-parkings'),
    path('building/<int:building_id>/parking/<int:parking_id>/', views.parking_detail_in_building, name='building-parking-detail'),

    path('building/<int:building_id>/warehouse/', views.BuildingViewSet.as_view({'get': 'warehouses'}), name='building-warehouses'),
    path('building/<int:building_id>/warehouse/<int:warehouse_id>/', views.warehouse_detail_in_building, name='building-warehouse-detail'),

    # existing unit-level helper endpoints
    path('unit/<int:unit_id>/transfer-history/', views.unit_transfer_history),
    path('unit/<int:unit_id>/change-ownership/', views.change_unit_ownership),
    path('unit/<int:unit_id>/change-residency/', views.change_unit_residency),
]