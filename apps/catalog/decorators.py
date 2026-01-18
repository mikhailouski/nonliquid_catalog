from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Product, Subdivision

def can_edit_product(view_func):
    """Декоратор для проверки прав на редактирование продукта"""
    def wrapper(request, *args, **kwargs):
        product_id = kwargs.get('pk') or kwargs.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        if not product.can_edit(request.user):
            raise PermissionDenied("У вас нет прав для редактирования этого продукта")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def can_delete_product(view_func):
    """Декоратор для проверки прав на удаление продукта"""
    def wrapper(request, *args, **kwargs):
        product_id = kwargs.get('pk')
        product = get_object_or_404(Product, id=product_id)
        
        if not product.can_delete(request.user):
            raise PermissionDenied("У вас нет прав для удаления этого продукта")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def can_add_to_subdivision(view_func):
    """Декоратор для проверки прав на добавление продукта в подразделение"""
    def wrapper(request, *args, **kwargs):
        subdivision_code = kwargs.get('subdivision_code')
        subdivision = get_object_or_404(Subdivision, code=subdivision_code)
        
        if not subdivision.can_add_product(request.user):
            raise PermissionDenied("У вас нет прав для добавления продуктов в это подразделение")
        
        return view_func(request, *args, **kwargs)
    return wrapper
