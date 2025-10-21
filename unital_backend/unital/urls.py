from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # تولید فایل OpenAPI به‌صورت JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # نمایش مستندات در Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    path('api/auth/', include('apps.accounts.urls')),
    path('api/complexes/', include('apps.complexes.urls')),
    path('api/financial/', include('apps.financial.urls')),
    path('api/operations/', include('apps.operations.urls')),
    path('api/communications/', include('apps.communications.urls')),
    path('api/facilities/', include('apps.facilities.urls')),
]