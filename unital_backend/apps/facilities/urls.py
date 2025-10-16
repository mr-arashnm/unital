from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'facilities', views.FacilityViewSet)
router.register(r'bookings', views.FacilityBookingViewSet)
router.register(r'maintenances', views.FacilityMaintenanceViewSet)
router.register(r'usage-rules', views.FacilityUsageRuleViewSet)
router.register(r'images', views.FacilityImageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]