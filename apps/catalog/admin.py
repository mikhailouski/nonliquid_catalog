from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Subdivision, Product, ProductImage, ChangeLog

class ProfileInline(admin.StackedInline):
    """Inline для отображения профиля в админке пользователя"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор подразделений только теми, где пользователь не является членом"""
        if db_field.name == "subdivision":
            # Получаем текущего пользователя (если редактируем существующего)
            if request.resolver_match.kwargs.get('object_id'):
                user_id = request.resolver_match.kwargs['object_id']
                current_profile = Profile.objects.filter(user_id=user_id).first()
                if current_profile and current_profile.subdivision:
                    # Исключаем текущее подразделение из queryset
                    kwargs["queryset"] = Subdivision.objects.exclude(
                        id=current_profile.subdivision.id
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class UserAdmin(BaseUserAdmin):
    """Кастомная админка пользователей с отображением подразделения"""
    inlines = [ProfileInline]
    list_display = BaseUserAdmin.list_display + ('get_subdivision', 'get_groups_display')
    
    def get_subdivision(self, obj):
        """Получить подразделение пользователя"""
        if hasattr(obj, 'profile') and obj.profile.subdivision:
            url = reverse('admin:catalog_subdivision_change', args=[obj.profile.subdivision.id])
            return format_html('<a href="{}">{}</a>', url, obj.profile.subdivision)
        return "—"
    get_subdivision.short_description = "Подразделение"
    
    def get_groups_display(self, obj):
        """Отобразить группы пользователя"""
        groups = obj.groups.all()
        if groups:
            return ", ".join([group.name for group in groups])
        return "—"
    get_groups_display.short_description = "Группы"
    
    def get_inline_instances(self, request, obj=None):
        """Показываем inline только при редактировании существующего пользователя"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class SubdivisionMemberInline(admin.TabularInline):
    """Inline для отображения членов подразделения"""
    model = Profile
    verbose_name = "Член подразделения"
    verbose_name_plural = "Члены подразделения"
    fields = ['user_link', 'phone', 'position']
    readonly_fields = ['user_link']
    extra = 0
    can_delete = False
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = "Пользователь"
    
    def has_add_permission(self, request, obj):
        return False

class SubdivisionAdminForm(forms.ModelForm):
    """Форма подразделения с возможностью добавления пользователя"""
    add_user = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__subdivision__isnull=True),
        required=False,
        label="Добавить пользователя в подразделение",
        help_text="Выберите пользователя, который еще не привязан к другому подразделению"
    )
    
    class Meta:
        model = Subdivision
        fields = '__all__'

@admin.register(Subdivision)
class SubdivisionAdmin(admin.ModelAdmin):
    form = SubdivisionAdminForm
    list_display = ['code', 'name', 'manager', 'product_count', 'member_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SubdivisionMemberInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description', 'manager')
        }),
        ('Управление пользователями', {
            'fields': ('add_user',),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        count = obj.members.count()
        return format_html('<strong>{}</strong>', count)
    member_count.short_description = "Кол-во членов"
    
    def product_count(self, obj):
        count = obj.product_count()
        url = reverse('admin:catalog_product_changelist') + f'?subdivision__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = "Кол-во неликвидов"
    
    def save_model(self, request, obj, form, change):
        # Сохраняем подразделение
        super().save_model(request, obj, form, change)
        
        # Добавляем пользователя в подразделение, если выбран
        add_user = form.cleaned_data.get('add_user')
        if add_user:
            # Создаем или обновляем профиль пользователя
            profile, created = Profile.objects.get_or_create(user=add_user)
            profile.subdivision = obj
            profile.save()
            
            # Логируем действие
            from django.contrib import messages
            messages.success(
                request, 
                f'Пользователь {add_user.username} добавлен в подразделение {obj.name}'
            )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subdivision', 'phone', 'position', 'created_at']
    list_filter = ['subdivision', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'position']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'subdivision')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'position')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор подразделений"""
        if db_field.name == "subdivision":
            # Если редактируем существующий профиль
            if request.resolver_match.kwargs.get('object_id'):
                profile_id = request.resolver_match.kwargs['object_id']
                current_profile = Profile.objects.filter(id=profile_id).first()
                if current_profile and current_profile.subdivision:
                    # Исключаем текущее подразделение из queryset
                    kwargs["queryset"] = Subdivision.objects.exclude(
                        id=current_profile.subdivision.id
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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