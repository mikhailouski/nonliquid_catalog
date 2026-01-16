from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Subdivision, Product, ProductImage, ChangeLog

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']
    fields = ['image', 'image_preview', 'is_main', 'description']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Превью"

class ChangeLogInline(admin.TabularInline):
    model = ChangeLog
    extra = 0
    readonly_fields = ['action', 'changed_by', 'changes', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Subdivision)
class SubdivisionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'manager', 'product_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description', 'manager')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.product_count()
        url = reverse('admin:catalog_product_changelist') + f'?subdivision__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = "Кол-во неликвидов"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'code', 
        'name', 
        'subdivision_link', 
        'status_badge', 
        'condition_display',
        'quantity',
        'created_by',
        'created_at'
    ]
    list_filter = ['status', 'condition', 'subdivision', 'created_at']
    search_fields = ['code', 'name', 'description', 'location']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'main_image_preview']
    list_select_related = ['subdivision', 'created_by']
    inlines = [ProductImageInline, ChangeLogInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description', 'characteristics')
        }),
        ('Классификация', {
            'fields': ('subdivision', 'status', 'condition')
        }),
        ('Количественные данные', {
            'fields': ('quantity', 'unit', 'location', 'storage_date')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'main_image_preview')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subdivision_link(self, obj):
        url = reverse('admin:catalog_subdivision_change', args=[obj.subdivision.id])
        return format_html('<a href="{}">{}</a>', url, obj.subdivision)
    subdivision_link.short_description = "Подразделение"
    
    def status_badge(self, obj):
        status_colors = {
            'available': 'green',
            'reserved': 'orange',
            'used': 'blue',
            'written_off': 'red',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"
    status_badge.admin_order_field = 'status'
    
    def condition_display(self, obj):
        return obj.get_condition_display()
    condition_display.short_description = "Состояние"
    condition_display.admin_order_field = 'condition'
    
    def main_image_preview(self, obj):
        main_image = obj.get_main_image()
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                main_image.image.url
            )
        return "Нет изображения"
    main_image_preview.short_description = "Основное изображение"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый объект
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product_link', 'image_preview', 'is_main', 'uploaded_by', 'uploaded_at']
    list_filter = ['is_main', 'uploaded_at']
    search_fields = ['product__code', 'product__name', 'description']
    readonly_fields = ['uploaded_by', 'uploaded_at', 'image_preview_large']
    
    def product_link(self, obj):
        url = reverse('admin:catalog_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product)
    product_link.short_description = "Продукт"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Превью"
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 300px;" />',
                obj.image.url
            )
        return "-"
    image_preview_large.short_description = "Изображение"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый объект
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'action', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['product__code', 'product__name', 'changed_by__username']
    readonly_fields = ['product', 'action', 'changed_by', 'changes', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False