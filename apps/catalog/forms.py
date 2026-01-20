from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, ProductImage, Subdivision, User

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'code', 'name', 'description', 'characteristics',
            'subdivision', 'status', 'condition', 'quantity',
            'unit', 'location', 'storage_date', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите код продукции'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите описание продукции'
            }),
            'characteristics': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"цвет": "красный", "размер": "10x20 см"}'
            }),
            'subdivision': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'шт., кг., м. и т.д.'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите место хранения'
            }),
            'storage_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки'
            }),
        }
        
        help_texts = {
            'code': 'Уникальный код продукции (артикул, серийный номер). Должен быть уникальным в пределах подразделения.',
            'characteristics': 'Можно оставить пустым или использовать формат: {"цвет": "красный", "вес": "10кг"}',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        subdivision = cleaned_data.get('subdivision')
        
        # Проверяем уникальность только при создании нового продукта
        if self.instance.pk is None and code and subdivision:
            if Product.objects.filter(
                code=code, 
                subdivision=subdivision
            ).exists():
                self.add_error(
                    'code', 
                    f'Продукт с кодом "{code}" уже существует в подразделении "{subdivision.name}"'
                )
        
        return cleaned_data

class ProductCreateWithImagesForm(ProductForm):
    """Форма создания продукта с загрузкой изображений"""
    # Это поле НЕ будет сохранено в модель Product, оно используется только для загрузки файлов
    images = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'd-none',
            'accept': 'image/*',
            'id': 'image-upload',
        }),
        label="",
        help_text=""
    )
    
    class Meta:
        model = Product
        fields = [
            'code', 'name', 'description', 'characteristics',
            'subdivision', 'status', 'condition', 'quantity',
            'unit', 'location', 'storage_date', 'notes'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите код продукции'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите описание продукции'
            }),
            'characteristics': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"цвет": "красный", "размер": "10x20 см"}'
            }),
            'subdivision': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'шт., кг., м. и т.д.'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите место хранения'
            }),
            'storage_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки'
            }),
        }
    
    def clean_images(self):
        # Мы не валидируем здесь, так как поле используется только для JavaScript
        return self.files.getlist('images') if 'images' in self.files else []

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'description', 'is_main']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Описание изображения'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class MultipleImageUploadForm(forms.Form):
    """Форма для множественной загрузки изображений"""
    images = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'd-none',
            'accept': 'image/*',
            'id': 'drag-drop-input'
        }),
        label="",
        help_text=""
    )
    
    def clean_images(self):
        files = self.files.getlist('images')
        if not files:
            raise forms.ValidationError("Не выбрано ни одного файла")
        
        for file in files:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    f"Файл {file.name} слишком большой. Максимальный размер: 10MB"
                )
            
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                raise forms.ValidationError(
                    f"Файл {file.name} имеет недопустимое расширение"
                )
        
        return files