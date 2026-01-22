import os
import platform
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('nonliquid_catalog')

# Загружаем настройки из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Для Windows используем threads вместо prefork
if platform.system() == 'Windows':
    app.conf.worker_pool = 'solo'  # или 'threads'
    app.conf.worker_concurrency = 1

# Автоматически находим задачи в установленных приложениях
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')