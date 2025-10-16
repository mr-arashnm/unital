from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh-token/', views.refresh_token_view, name='refresh-token'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-account/', views.verify_account_view, name='verify-account'),
    path('reset-password-request/', views.reset_password_request_view, name='reset-password-request'),
    path('reset-password-confirm/', views.reset_password_confirm_view, name='reset-password-confirm'),
    path('my-complexes/', views.user_complexes_view, name='user-complexes'),
]