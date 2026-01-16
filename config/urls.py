from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.catalog.forms import CustomLoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ОЧЕНЬ ВАЖНО: login должен быть определен ДО include
    path('login/', 
         auth_views.LoginView.as_view(
             template_name='catalog/login.html',
             authentication_form=CustomLoginForm,
             redirect_authenticated_user=True
         ), 
         name='login'),
    path('logout/', 
         auth_views.LogoutView.as_view(next_page='home'), 
         name='logout'),
    
    # Все остальные пути каталога
    path('', include('apps.catalog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Панель администратора каталога неликвидов"
admin.site.site_title = "Каталог неликвидов"
admin.site.index_title = "Управление каталогом"