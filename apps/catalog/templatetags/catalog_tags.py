from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Возвращает цвет для статуса"""
    colors = {
        'available': '#27ae60',
        'reserved': '#f39c12',
        'used': '#3498db',
        'written_off': '#e74c3c',
    }
    return colors.get(status, '#95a5a6')

@register.filter
def status_class(status):
    """Возвращает CSS класс для статуса"""
    classes = {
        'available': 'status-available',
        'reserved': 'status-reserved',
        'used': 'status-used',
        'written_off': 'status-written_off',
    }
    return classes.get(status, 'status-default')

@register.filter
def can_add_product(subdivision, user):
    """Проверяет, может ли пользователь добавлять продукты в подразделение"""
    return subdivision.can_add_product(user)    