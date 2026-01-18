from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import os

def validate_image_size(value):
    """Валидатор для проверки размера изображения (макс 10MB)"""
    filesize = value.size
    max_size = 10 * 1024 * 1024  # 10MB
    if filesize > max_size:
        raise ValidationError(
            f"Максимальный размер файла {max_size//1024//1024}MB. "
            f"Ваш файл {filesize//1024//1024}MB"
        )

def get_image_upload_path(instance, filename):
    """Генерация пути для загрузки изображений"""
    return f'product_images/{instance.product.subdivision.code}/{instance.product.code}/{filename}'

def get_thumbnail_upload_path(instance, filename):
    """Генерация пути для загрузки миниатюр"""
    return f'product_thumbnails/{instance.product.subdivision.code}/{instance.product.code}/{filename}'

class Subdivision(models.Model):
    """Модель подразделения предприятия"""
    name = models.CharField(
        max_length=200, 
        verbose_name="Название подразделения",
        help_text="Полное название подразделения"
    )
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Код подразделения",
        help_text="Уникальный код подразделения (например, ЦЕХ-01)"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Описание",
        help_text="Дополнительная информация о подразделении"
    )
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_subdivisions',
        verbose_name="Руководитель подразделения",
        help_text="Ответственный за подразделение"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def product_count(self):
        """Количество неликвидов в подразделении"""
        return self.products.count()
    
    product_count.short_description = "Количество неликвидов"

    def can_add_product(self, user):
        """Проверяет, может ли пользователь добавлять продукты в подразделение"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Руководитель подразделения
        if self.manager == user:
            return True
        
        # Проверка через группы
        if user.groups.filter(name__in=['Super_Admin', 'Subdivision_Admin', 'Editor']).exists():
            return True
            
        return False
    
    # Для использования в шаблонах
    def user_can_add_product(self, user):
        """Альтернативный метод для шаблонов"""
        return self.can_add_product(user)

class Product(models.Model):
    """Модель неликвидной продукции"""
    
    STATUS_CHOICES = [
        ('available', '✅ Доступен'),
        ('reserved', '⏳ Зарезервирован'),
        ('used', '✅ Использован'),
        ('written_off', '❌ Списано'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'Новое'),
        ('used', 'Б/у'),
        ('defective', 'Неисправное'),
        ('for_parts', 'На запчасти'),
    ]
    
    code = models.CharField(
        max_length=100, 
        verbose_name="Код продукции",
        db_index=True,
        help_text="Уникальный код продукции (артикул, серийный номер)"
    )
    name = models.CharField(
        max_length=200, 
        verbose_name="Наименование",
        help_text="Полное наименование продукции"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Описание",
        help_text="Подробное описание продукции"
    )
    characteristics = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name="Характеристики",
        help_text="Дополнительные характеристики в формате ключ-значение"
    )
    subdivision = models.ForeignKey(
        Subdivision, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name="Подразделение"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_products',
        verbose_name="Кем создан",
        editable=False
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='available',
        verbose_name="Статус"
    )
    condition = models.CharField(
        max_length=20, 
        choices=CONDITION_CHOICES, 
        default='used',
        verbose_name="Состояние"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество",
        validators=[MinValueValidator(1), MaxValueValidator(99999)]
    )
    unit = models.CharField(
        max_length=20,
        default='шт.',
        verbose_name="Единица измерения",
        help_text="шт., кг., м., упак."
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Место хранения",
        help_text="Конкретное место хранения на складе/в цехе"
    )
    storage_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата постановки на хранение"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Примечания",
        help_text="Дополнительные заметки"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Неликвид"
        verbose_name_plural = "Неликвиды"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['subdivision']),
            models.Index(fields=['status']),
            models.Index(fields=['condition']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['code', 'subdivision'],
                name='unique_product_code_per_subdivision'
            )
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_main_image(self):
        """Получение основного изображения продукта"""
        main_image = self.images.filter(is_main=True).first()
        if main_image:
            return main_image
        return self.images.first()
    
    def save(self, *args, **kwargs):
        """Переопределение save для логирования изменений"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Здесь позже добавим логирование изменений
        if not is_new:
            # Логирование изменения
            pass

    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать продукт"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Руководитель подразделения
        if self.subdivision.manager == user:
            return True
        
        # Создатель продукта
        if self.created_by == user:
            return True
        
        # Проверка через группы
        if user.groups.filter(name__in=['Super_Admin', 'Subdivision_Admin']).exists():
            return True
        
        # Editor может редактировать только свои продукты
        if user.groups.filter(name='Editor').exists() and self.created_by == user:
            return True
            
        return False
    
    def can_delete(self, user):
        """Проверяет, может ли пользователь удалить продукт"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Только супер-админы и администраторы подразделений могут удалять
        if user.groups.filter(name__in=['Super_Admin', 'Subdivision_Admin']).exists():
            return True
            
        return False

class ProductImage(models.Model):
    """Модель для хранения изображений продуктов"""
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Продукт"
    )
    image = models.ImageField(
        upload_to=get_image_upload_path,
        verbose_name="Оригинальное изображение",
        validators=[validate_image_size],
        help_text="Максимальный размер файла: 10MB"
    )
    thumbnail = models.ImageField(
        upload_to=get_thumbnail_upload_path,
        null=True,
        blank=True,
        verbose_name="Миниатюра",
        editable=False
    )
    is_main = models.BooleanField(
        default=False, 
        verbose_name="Основное изображение",
        help_text="Отметьте, если это основное изображение продукта"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Описание изображения"
    )
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        editable=False,
        verbose_name="Кем загружено"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    
    class Meta:
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"
        ordering = ['-is_main', 'uploaded_at']
    
    def __str__(self):
        return f"Изображение для {self.product.code}"
    
    def save(self, *args, **kwargs):
        """Переопределение save для обработки изображений"""
        is_new = self.pk is None
        
        # Если это новое изображение и нет других изображений у продукта,
        # делаем его основным
        if is_new and not self.product.images.exists():
            self.is_main = True
        
        # Проверяем, чтобы было только одно основное изображение
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product, 
                is_main=True
            ).exclude(pk=self.pk).update(is_main=False)
        
        super().save(*args, **kwargs)
        
        # Если это новое изображение, запускаем обработку
        if is_new:
            try:
                from .tasks import process_product_image
                process_product_image.delay(self.id)
            except Exception as e:
                # Логируем ошибку, но не прерываем сохранение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка при запуске обработки изображения: {e}")

class ChangeLog(models.Model):
    """Модель для отслеживания изменений в продуктах"""
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('status_change', 'Изменение статуса'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='changes',
        verbose_name="Продукт"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Действие")
    changed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Кем изменено"
    )
    changes = models.JSONField(
        default=dict,
        verbose_name="Изменения",
        help_text="Детали изменений в формате JSON"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время изменения")
    
    class Meta:
        verbose_name = "История изменений"
        verbose_name_plural = "История изменений"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.product.code}"