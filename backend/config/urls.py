from django.contrib import admin
from django.urls import include, path

from monitoring import views as status

admin.site.site_header = 'Richard Kwanya Snr — Ministry Admin'
admin.site.site_title = 'RK Ministry Admin'
admin.site.index_title = 'Manage website content'


urlpatterns = [
    path('', status.status_page),
    path('health/', status.health),
    path('admin/', admin.site.urls),
    path('api/manage/', include('panel.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('content.urls')),
    path('api/', include('shop.urls')),
    path('api/', include('newsletter.urls')),
    path('api/test/', lambda request: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'newsletter_loaded': 'newsletter' in __import__('django.apps', fromlist=['apps']).apps.app_configs}), name='test'),
]
