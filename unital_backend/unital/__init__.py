from django.contrib.admin import sites

class CustomAdminSite(sites.AdminSite):
    site_header = 'مدیریت Unital'
    site_title = 'پنل مدیریت Unital'
    index_title = 'خوش آمدید به پنل مدیریت Unital'

admin_site = CustomAdminSite(name='custom_admin')