import os
from celery import shared_task
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from .models import ProductImage

@shared_task
def create_thumbnail(image_id):
    """Создание миниатюры для изображения продукта"""
    try:
        product_image = ProductImage.objects.get(id=image_id)
        
        # Открываем оригинальное изображение
        img = Image.open(product_image.image.path)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Создаем миниатюру (500x500)
        img.thumbnail((500, 500), Image.Resampling.LANCZOS)
        
        # Сохраняем миниатюру
        thumb_name = f"thumb_{os.path.basename(product_image.image.name)}"
        thumb_path = os.path.join(
            settings.MEDIA_ROOT,
            'product_thumbnails',
            thumb_name
        )
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        
        # Сохраняем изображение
        img.save(thumb_path, 'JPEG', quality=85)
        
        # Обновляем модель
        product_image.thumbnail.name = f'product_thumbnails/{thumb_name}'
        product_image.save(update_fields=['thumbnail'])
        
        return f"Миниатюра создана для {product_image.id}"
        
    except ProductImage.DoesNotExist:
        return f"Изображение {image_id} не найдено"
    except Exception as e:
        return f"Ошибка при создании миниатюры: {str(e)}"

@shared_task
def optimize_image(image_id):
    """Оптимизация оригинального изображения"""
    try:
        product_image = ProductImage.objects.get(id=image_id)
        
        # Открываем оригинальное изображение
        img = Image.open(product_image.image.path)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Определяем максимальный размер
        max_size = (1920, 1080)  # Full HD
        
        # Масштабируем если изображение слишком большое
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Сохраняем оптимизированное изображение
        buffer = BytesIO()
        img.save(buffer, 'JPEG', quality=85, optimize=True)
        
        # Перезаписываем оригинальный файл
        product_image.image.save(
            os.path.basename(product_image.image.name),
            ContentFile(buffer.getvalue()),
            save=True
        )
        
        return f"Изображение оптимизировано для {product_image.id}"
        
    except ProductImage.DoesNotExist:
        return f"Изображение {image_id} не найдено"
    except Exception as e:
        return f"Ошибка при оптимизации: {str(e)}"

@shared_task
def process_product_image(image_id):
    """Полная обработка изображения: оптимизация + создание миниатюры"""
    optimize_result = optimize_image(image_id)
    thumbnail_result = create_thumbnail(image_id)
    
    return {
        'optimize': optimize_result,
        'thumbnail': thumbnail_result
    }

@shared_task
def process_multiple_images(image_ids):
    """Обработка нескольких изображений"""
    results = []
    for image_id in image_ids:
        result = process_product_image.delay(image_id)
        results.append((image_id, result.id))
    
    return {
        'total': len(image_ids),
        'tasks': results
    }