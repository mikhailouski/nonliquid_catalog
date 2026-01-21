from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.catalog.forms import CustomLoginForm
from apps.catalog.views import custom_logout, logout_confirmation

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Вход
    path('login/', 
         auth_views.LoginView.as_view(
             template_name='catalog/login.html',
             authentication_form=CustomLoginForm,
             redirect_authenticated_user=True
         ), 
         name='login'),
    
    # Выход - ДОЛЖЕН БЫТЬ ЗДЕСЬ, перед include
    path('logout/', custom_logout, name='logout'),
    path('logout/confirmation/', logout_confirmation, name='logout_confirmation'),
    
    # Все остальные пути каталога
    path('', include('apps.catalog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Панель администратора каталога неликвидов"
admin.site.site_title = "Каталог неликвидов"
admin.site.index_title = "Управление каталогом"