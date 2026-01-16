from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.catalog.models import Subdivision, Product, ProductImage

class Command(BaseCommand):
    help = 'Создает стандартные группы пользователей и назначает права'

    def handle(self, *args, **kwargs):
        # Создаем группы
        groups = [
            ('Viewer', 'Только просмотр'),
            ('Editor', 'Добавление и редактирование своих записей'),
            ('Subdivision_Admin', 'Администратор подразделения'),
            ('Super_Admin', 'Супер администратор'),
        ]

        # Права для каждой группы
        group_permissions = {
            'Viewer': [
                'view_subdivision',
                'view_product',
                'view_productimage',
            ],
            'Editor': [
                'view_subdivision',
                'view_product',
                'view_productimage',
                'add_product',
                'change_product',
                'add_productimage',
                'change_productimage',
            ],
            'Subdivision_Admin': [
                'view_subdivision',
                'view_product',
                'view_productimage',
                'add_product',
                'change_product',
                'delete_product',
                'add_productimage',
                'change_productimage',
                'delete_productimage',
            ],
            'Super_Admin': [
                # Все права
            ]
        }

        for group_name, group_desc in groups:
            group, created = Group.objects.get_or_create(
                name=group_name,
                defaults={'name': group_name}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Группа "{group_name}" создана')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Группа "{group_name}" уже существует')
                )

            # Назначаем права для группы
            if group_name in group_permissions:
                if group_name == 'Super_Admin':
                    # Супер-админы получают все права
                    permissions = Permission.objects.all()
                else:
                    # Для остальных групп назначаем конкретные права
                    permissions = Permission.objects.filter(
                        codename__in=group_permissions[group_name]
                    )
                
                group.permissions.set(permissions)
                self.stdout.write(
                    self.style.SUCCESS(f'Права назначены для группы "{group_name}"')
                )

        self.stdout.write(
            self.style.SUCCESS('Все группы пользователей созданы и настроены!')
        )