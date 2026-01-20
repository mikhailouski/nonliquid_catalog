from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.catalog.models import Subdivision, UserSubdivisionAccess

class Command(BaseCommand):
    help = 'Миграция существующих прав пользователей на новую систему'

    def handle(self, *args, **kwargs):
        # Создаем доступы для руководителей подразделений
        for subdivision in Subdivision.objects.all():
            if subdivision.manager:
                access, created = UserSubdivisionAccess.objects.get_or_create(
                    user=subdivision.manager,
                    subdivision=subdivision,
                    defaults={
                        'access_level': 'manager',
                        'granted_by': User.objects.filter(is_superuser=True).first()
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Создан доступ MANAGER для {subdivision.manager.username} в {subdivision.code}')
                    )

        # Мигрируем права по группам
        groups_mapping = {
            'Editor': 'editor',
            'Subdivision_Admin': 'admin',
            'Super_Admin': 'admin',  # Super_Admin будет иметь admin доступ во всех подразделениях
            'Viewer': 'viewer',
        }

        for group_name, access_level in groups_mapping.items():
            try:
                group = Group.objects.get(name=group_name)
                users = group.user_set.all()
                
                for user in users:
                    # Даем доступ ко всем подразделениям
                    for subdivision in Subdivision.objects.all():
                        # Проверяем, нет ли уже доступа (например, как руководитель)
                        if not UserSubdivisionAccess.objects.filter(
                            user=user, 
                            subdivision=subdivision
                        ).exists():
                            UserSubdivisionAccess.objects.create(
                                user=user,
                                subdivision=subdivision,
                                access_level=access_level,
                                granted_by=User.objects.filter(is_superuser=True).first()
                            )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Мигрирована группа {group_name}: {users.count()} пользователей')
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Группа {group_name} не найдена')
                )

        self.stdout.write(
            self.style.SUCCESS('\nМиграция завершена!')
        )