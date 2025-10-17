from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # avoid referencing created_at/updated_at here until DB migrations are applied
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active')
    list_filter = ('user_type', 'is_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'phone', 'national_code', 'avatar')}),
        ('دسترسی‌ها', {'fields': ('user_type', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('تاریخ‌ها', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'user_type'),
        }),
    )
    
    # keep last_login readonly; created_at/updated_at removed until migrations applied
    readonly_fields = ('last_login',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()