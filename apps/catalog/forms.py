from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, ProductImage, Subdivision

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
                'placeholder': 'Введите характеристики в формате JSON или текстом'
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
            'code': 'Уникальный код продукции (артикул, серийный номер)',
            'characteristics': 'Можно оставить пустым или использовать формат: {"цвет": "красный", "вес": "10кг"}',
        }

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
    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'multiple': False,
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label="Изображения",
        help_text="Можно выбрать несколько файлов. Максимальный размер каждого файла: 10MB"
    )
    
    def clean_images(self):
        images = self.files.getlist('images')
        for image in images:
            if image.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(
                    f"Файл {image.name} слишком большой. Максимальный размер: 10MB"
                )
        return images