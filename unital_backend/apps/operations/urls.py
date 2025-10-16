from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'teams', views.TeamViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'service-requests', views.ServiceRequestViewSet)
router.register(r'task-comments', views.TaskCommentViewSet)
router.register(r'performance', views.PerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]