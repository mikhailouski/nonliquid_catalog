from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

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

@register.filter
def highlight(text, query):
    """Подсветка найденного текста в результатах поиска"""
    if not text or not query:
        return text
    
    text_str = str(text)
    query_str = str(query)
    
    # Экранируем HTML
    text_str = escape(text_str)
    query_str = escape(query_str)
    
    # Находим все вхождения (регистронезависимо)
    import re
    pattern = re.compile(re.escape(query_str), re.IGNORECASE)
    
    # Заменяем найденное на подсвеченную версию
    highlighted = pattern.sub(
        lambda m: f'<span class="bg-warning">{m.group()}</span>',
        text_str
    )
    
    return mark_safe(highlighted)