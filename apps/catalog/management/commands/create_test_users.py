from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.catalog.models import Subdivision

class Command(BaseCommand):
    help = 'Создает тестовых пользователей для демонстрации'

    def handle(self, *args, **kwargs):
        # Пароль для всех тестовых пользователей
        password = 'testpass123'

        # Создаем тестовых пользователей
        test_users = [
            {
                'username': 'viewer_user',
                'email': 'viewer@example.com',
                'first_name': 'Иван',
                'last_name': 'Смотров',
                'groups': ['Viewer'],
            },
            {
                'username': 'editor_user',
                'email': 'editor@example.com',
                'first_name': 'Петр',
                'last_name': 'Редакторов',
                'groups': ['Editor'],
            },
            {
                'username': 'admin_ceh1',
                'email': 'admin_ceh1@example.com',
                'first_name': 'Анна',
                'last_name': 'Цехова',
                'groups': ['Subdivision_Admin'],
            },
            {
                'username': 'admin_ceh2',
                'email': 'admin_ceh2@example.com',
                'first_name': 'Сергей',
                'last_name': 'Складской',
                'groups': ['Subdivision_Admin'],
            },
            {
                'username': 'super_admin',
                'email': 'super@example.com',
                'first_name': 'Администратор',
                'last_name': 'Системный',
                'groups': ['Super_Admin'],
            },
        ]

        for user_data in test_users:
            # Проверяем, существует ли пользователь
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Пользователь {user_data["username"]} создан')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Пользователь {user_data["username"]} уже существует')
                )

            # Назначаем группы
            for group_name in user_data['groups']:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    self.stdout.write(
                        self.style.SUCCESS(f'Группа {group_name} назначена пользователю {user_data["username"]}')
                    )
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Группа {group_name} не найдена')
                    )

        # Создаем подразделения и назначаем руководителей
        subdivisions = [
            {
                'code': 'CEH-01',
                'name': 'Цех №1 - Механосборочный',
                'manager_username': 'admin_ceh1',
            },
            {
                'code': 'CEH-02',
                'name': 'Цех №2 - Инструментальный',
                'manager_username': 'admin_ceh2',
            },
            {
                'code': 'SKLAD',
                'name': 'Склад готовой продукции',
                'manager_username': 'editor_user',
            },
        ]

        for sub_data in subdivisions:
            try:
                manager = User.objects.get(username=sub_data['manager_username'])
                subdivision, created = Subdivision.objects.get_or_create(
                    code=sub_data['code'],
                    defaults={
                        'name': sub_data['name'],
                        'manager': manager,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Подразделение {sub_data["code"]} создано')
                    )
                else:
                    # Обновляем руководителя, если подразделение уже существует
                    subdivision.manager = manager
                    subdivision.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Руководитель обновлен для подразделения {sub_data["code"]}')
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Пользователь {sub_data["manager_username"]} не найден')
                )

        self.stdout.write(
            self.style.SUCCESS('\nТестовые пользователи созданы!')
        )
        self.stdout.write(
            self.style.NOTICE('\nДанные для входа:')
        )
        self.stdout.write(
            self.style.NOTICE('Логин: viewer_user, editor_user, admin_ceh1, admin_ceh2, super_admin')
        )
        self.stdout.write(
            self.style.NOTICE('Пароль для всех: testpass123')
        )