from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet)
router.register(r'meetings', views.MeetingViewSet)
router.register(r'meeting-minutes', views.MeetingMinuteViewSet)
router.register(r'meeting-attendance', views.MeetingAttendanceViewSet)
router.register(r'announcements', views.AnnouncementViewSet)
router.register(r'support-tickets', views.SupportTicketViewSet)
router.register(r'ticket-responses', views.TicketResponseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]