from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.HomeView.as_view(), name='home'),
    
    # Профиль пользователя (должен быть ДО подразделений)
    path('profile/', views.user_profile, name='user_profile'),
    
    # Поиск (должен быть ДО подразделений)
    path('search/', views.search_products, name='search_products'),
    
    # Загрузка изображений (должна быть ДО подразделений)
    path('upload-images/<int:product_id>/', 
         views.upload_product_images, name='upload_product_images'),
    
    # CRUD операции (должны быть ДО подразделений)
    path('create/<str:subdivision_code>/', 
         views.ProductCreateView.as_view(), name='product_create'),
    path('update/<int:pk>/', 
         views.ProductUpdateView.as_view(), name='product_update'),
    path('delete/<int:pk>/', 
         views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Детальная страница продукта (новая структура)
    path('product/<int:product_id>/in/<str:subdivision_code>/', 
         views.ProductDetailView.as_view(), name='product_detail'),
    
    # Подразделения (В САМОМ КОНЦЕ)
    path('<str:subdivision_code>/', views.SubdivisionProductsView.as_view(), 
         name='subdivision_products'),
]