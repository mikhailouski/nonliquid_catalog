// Функции для загрузки изображений

class ImageUploader {
    constructor(options = {}) {
        this.options = {
            uploadUrl: '',
            maxFiles: 10,
            maxSize: 10 * 1024 * 1024, // 10MB
            allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/bmp'],
            csrfToken: '',
            ...options
        };
        
        this.files = [];
        this.initialize();
    }
    
    initialize() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Drag and drop
        const dropZone = document.querySelector('.upload-area');
        if (dropZone) {
            dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
            dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
            dropZone.addEventListener('drop', this.handleDrop.bind(this));
        }
        
        // File input change
        const fileInput = document.getElementById('image-upload');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }
        
        // Browse button
        const browseBtn = document.getElementById('browse-btn');
        if (browseBtn) {
            browseBtn.addEventListener('click', () => fileInput.click());
        }
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
        // Сбросить input
        e.target.value = '';
    }
    
    processFiles(files) {
        const validFiles = [];
        const errors = [];
        
        files.forEach(file => {
            // Проверка типа файла
            if (!this.options.allowedTypes.includes(file.type)) {
                errors.push(`Файл "${file.name}" имеет недопустимый тип`);
                return;
            }
            
            // Проверка размера
            if (file.size > this.options.maxSize) {
                errors.push(`Файл "${file.name}" слишком большой (${this.formatBytes(file.size)})`);
                return;
            }
            
            // Проверка количества файлов
            if (this.files.length + validFiles.length >= this.options.maxFiles) {
                errors.push(`Максимальное количество файлов: ${this.options.maxFiles}`);
                return;
            }
            
            validFiles.push(file);
        });
        
        // Показать ошибки
        if (errors.length > 0) {
            this.showErrors(errors);
        }
        
        // Добавить валидные файлы
        if (validFiles.length > 0) {
            this.files.push(...validFiles);
            this.createPreviews(validFiles);
            this.updateFileInput();
        }
    }
    
    createPreviews(files) {
        const container = document.getElementById('image-preview-container');
        if (!container) return;
        
        files.forEach(file => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const col = document.createElement('div');
                col.className = 'col-6 col-md-4 col-lg-3 mb-3';
                
                col.innerHTML = `
                    <div class="image-preview">
                        <img src="${e.target.result}" class="img-fluid rounded" alt="${file.name}">
                        <button type="button" class="remove-btn" data-filename="${file.name}">
                            <i class="bi bi-x"></i>
                        </button>
                        <div class="file-info small mt-1">
                            <div class="text-truncate">${file.name}</div>
                            <div class="text-muted">${this.formatBytes(file.size)}</div>
                        </div>
                    </div>
                `;
                
                container.appendChild(col);
                
                // Добавить обработчик удаления
                const removeBtn = col.querySelector('.remove-btn');
                removeBtn.addEventListener('click', () => {
                    this.removeFile(file.name);
                    col.remove();
                });
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    removeFile(filename) {
        this.files = this.files.filter(file => file.name !== filename);
        this.updateFileInput();
    }
    
    updateFileInput() {
        const fileInput = document.getElementById('image-upload');
        if (!fileInput) return;
        
        const dataTransfer = new DataTransfer();
        this.files.forEach(file => {
            dataTransfer.items.add(file);
        });
        
        fileInput.files = dataTransfer.files;
        
        // Обновить счетчик файлов
        this.updateFileCounter();
    }
    
    updateFileCounter() {
        const counter = document.getElementById('file-counter');
        if (counter) {
            counter.textContent = `Выбрано файлов: ${this.files.length}`;
        }
    }
    
    showErrors(errors) {
        // Можно реализовать красивый вывод ошибок
        if (errors.length > 0) {
            alert(errors.join('\n'));
        }
    }
    
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    async upload() {
        if (this.files.length === 0) {
            return { success: false, error: 'Нет файлов для загрузки' };
        }
        
        const formData = new FormData();
        
        // Добавляем CSRF токен
        formData.append('csrfmiddlewaretoken', this.options.csrfToken);
        
        // Добавляем файлы
        this.files.forEach(file => {
            formData.append('files', file);
        });
        
        try {
            const response = await fetch(this.options.uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    clear() {
        this.files = [];
        this.updateFileInput();
        
        const container = document.getElementById('image-preview-container');
        if (container) {
            container.innerHTML = '';
        }
    }
}

// Экспорт для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageUploader;
} else {
    window.ImageUploader = ImageUploader;
}