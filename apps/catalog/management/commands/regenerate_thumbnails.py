from django.core.management.base import BaseCommand
from django.db import transaction
from apps.catalog.models import ProductImage
from apps.catalog.tasks import create_thumbnail
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Пересоздает миниатюры для всех изображений'

    def add_arguments(self, parser):
        parser.add_argument(
            '--image_ids',
            nargs='+',
            type=int,
            help='ID конкретных изображений для обработки'
        )
        parser.add_argument(
            '--product_id',
            type=int,
            help='ID продукта, для которого пересоздать миниатюры'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать даже если миниатюра уже существует'
        )

    def handle(self, *args, **options):
        image_ids = options.get('image_ids')
        product_id = options.get('product_id')
        force = options.get('force', False)
        
        if image_ids:
            queryset = ProductImage.objects.filter(id__in=image_ids)
        elif product_id:
            queryset = ProductImage.objects.filter(product_id=product_id)
        else:
            queryset = ProductImage.objects.all()
        
        total = queryset.count()
        processed = 0
        failed = 0
        
        self.stdout.write(f"Найдено {total} изображений для обработки")
        
        for product_image in queryset:
            try:
                # Пропускаем, если миниатюра уже есть и не форсируем
                if product_image.thumbnail and not force:
                    self.stdout.write(
                        self.style.WARNING(f"Миниатюра уже существует для {product_image.id}")
                    )
                    continue
                
                # Запускаем задачу
                create_thumbnail.delay(product_image.id)
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Задача создана для изображения {product_image.id}")
                )
                
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"Ошибка для изображения {product_image.id}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Обработано: {processed}, ошибок: {failed}, всего: {total}"
            )
        )