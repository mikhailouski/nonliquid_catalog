from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.HomeView.as_view(), name='home'),
    
    # Профиль пользователя
    path('profile/', views.user_profile, name='user_profile'),
    
    # Поиск
    path('search/', views.search_products, name='search_products'),
    
    # Загрузка изображений (AJAX)
    path('ajax-upload/<int:product_id>/', 
         views.ajax_upload_images, name='ajax_upload_images'),
    
    # CRUD операции (ВАЖНО: порядок имеет значение!)
    path('create/<str:subdivision_code>/', 
         views.ProductCreateView.as_view(), name='product_create'),
    path('create-with-images/<str:subdivision_code>/', 
         views.ProductCreateWithImagesView.as_view(), name='product_create_with_images'),
    path('quick-create/<str:subdivision_code>/', 
         views.quick_product_create, name='quick_product_create'),
    path('update/<int:pk>/', 
         views.ProductUpdateView.as_view(), name='product_update'),
    path('delete/<int:pk>/', 
         views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Загрузка изображений
    path('upload-images/<int:product_id>/', 
         views.upload_product_images, name='upload_product_images'),
    
    # Подразделения и продукты
    path('product/<int:product_id>/in/<str:subdivision_code>/', 
         views.ProductDetailView.as_view(), name='product_detail'),
    path('<str:subdivision_code>/', views.SubdivisionProductsView.as_view(), 
         name='subdivision_products'),
]