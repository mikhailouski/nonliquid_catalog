// Основные JavaScript функции

// Подтверждение удаления
function confirmDelete(message) {
    return confirm(message || 'Вы уверены, что хотите удалить этот элемент?');
}

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Показать/скрыть пароль
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
        
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        new bootstrap.Alert(alert);
    });
    
    // Подсветка активных ссылок в навигации
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Замена битых изображений на заглушку
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            this.src = '/static/images/placeholder.jpg';
            this.alt = 'Изображение не загружено';
        });
    });
});

// Дополнительные функции для галереи

// Открытие изображения в новой вкладке при клике средней кнопкой мыши
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.gallery-thumbnail img').forEach(img => {
        img.addEventListener('auxclick', function(e) {
            if (e.button === 1) { // Средняя кнопка мыши
                e.preventDefault();
                window.open(this.src.replace('_thumb', ''), '_blank');
            }
        });
    });
});

// Функция для предзагрузки изображений галереи
function preloadGalleryImages(imageUrls) {
    imageUrls.forEach(url => {
        const img = new Image();
        img.src = url;
    });
}

// Улучшенная обработка ошибок загрузки изображений
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function() {
            // Если миниатюра не загрузилась, пробуем загрузить оригинал
            if (this.src.includes('_thumb') || this.src.includes('thumbnails')) {
                const originalUrl = this.src
                    .replace('_thumb', '')
                    .replace('thumbnails', 'images');
                
                // Создаем новое изображение для проверки
                const testImg = new Image();
                testImg.onload = () => {
                    this.src = originalUrl;
                };
                testImg.src = originalUrl;
            }
        });
    });
});