from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'complexes', views.ComplexViewSet)
router.register(r'buildings', views.BuildingViewSet)
router.register(r'units', views.UnitViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('units/<int:unit_id>/transfer-history/', views.unit_transfer_history, name='unit-transfer-history'),
    path('units/<int:unit_id>/change-ownership/', views.change_unit_ownership, name='change-unit-ownership'),
]