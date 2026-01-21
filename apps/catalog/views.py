from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
from .models import Subdivision, Product, ProductImage
from .forms import (
    ProductForm, MultipleImageUploadForm,
    ProductCreateWithImagesForm, 
)
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class HomeView(ListView):
    """Главная страница - список подразделений"""
    model = Subdivision
    template_name = 'catalog/home.html'
    context_object_name = 'subdivisions'
    
    def get_queryset(self):
        # Аннотируем количество продуктов в каждом подразделении
        return Subdivision.objects.annotate(
            product_count=Count('products')
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Общее количество неликвидов
        context['total_products'] = Product.objects.count()
        # Статистика по статусам
        context['status_stats'] = Product.objects.values('status').annotate(
            count=Count('id')
        )
        return context

class SubdivisionProductsView(ListView):
    """Список продуктов в подразделении"""
    model = Product
    template_name = 'catalog/subdivision_products.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        self.subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
        return Product.objects.filter(
            subdivision=self.subdivision
        ).select_related('subdivision', 'created_by').prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subdivision'] = self.subdivision
        
        # Проверяем права пользователя
        context['can_add_product'] = self.subdivision.can_user_add_product(self.request.user)
        
        # Получаем параметры фильтрации из GET-запроса
        status_filter = self.request.GET.get('status')
        condition_filter = self.request.GET.get('condition')
        
        # Применяем фильтры к queryset
        queryset = self.get_queryset()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if condition_filter:
            queryset = queryset.filter(condition=condition_filter)
        
        context['filtered_products'] = queryset
        context['status_filter'] = status_filter
        context['condition_filter'] = condition_filter
        
        return context

class ProductDetailView(DetailView):
    """Детальная страница продукта"""
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        # Новая структура URL: product/<id>/in/<subdivision_code>/
        product_id = self.kwargs['product_id']
        subdivision_code = self.kwargs['subdivision_code']
        
        return get_object_or_404(
            Product.objects.select_related('subdivision', 'created_by')
                          .prefetch_related('images'),
            id=product_id,
            subdivision__code=subdivision_code
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_image'] = self.object.get_main_image()
        context['other_images'] = self.object.images.exclude(
            id=context['main_image'].id if context['main_image'] else None
        )
        
        # Проверяем права пользователя
        context['can_edit'] = self.object.can_edit(self.request.user)
        context['can_delete'] = self.object.can_delete(self.request.user)
        context['can_upload_images'] = self.object.can_edit(self.request.user)
        
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    """Создание нового продукта (базовый класс)"""
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subdivision'] = self.subdivision
        
        # Проверяем права пользователя
        context['can_add_product'] = self.subdivision.can_user_add_product(self.request.user)
        
        # Получаем параметры фильтрации из GET-запроса
        status_filter = self.request.GET.get('status')
        condition_filter = self.request.GET.get('condition')
        
        # Применяем фильтры к queryset
        queryset = self.get_queryset()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if condition_filter:
            queryset = queryset.filter(condition=condition_filter)
        
        context['filtered_products'] = queryset
        context['status_filter'] = status_filter
        context['condition_filter'] = condition_filter
        
        return context
    
    def get_initial(self):
        """Устанавливаем подразделение по умолчанию"""
        initial = super().get_initial()
        initial['subdivision'] = self.subdivision
        return initial
    
    def get_form_kwargs(self):
        """Передаем подразделение в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['initial']['subdivision'] = self.subdivision
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Добавляем subdivision в контекст"""
        context = super().get_context_data(**kwargs)
        context['subdivision'] = self.subdivision
        return context
    
    def form_valid(self, form):
        # Проверяем уникальность кода в подразделении
        code = form.cleaned_data.get('code')
        
        # Проверяем, существует ли уже продукт с таким кодом в этом подразделении
        if Product.objects.filter(
            code=code, 
            subdivision=self.subdivision
        ).exists():
            form.add_error(
                'code', 
                f'Продукт с кодом "{code}" уже существует в подразделении "{self.subdivision.name}"'
            )
            return self.form_invalid(form)
        
        form.instance.created_by = self.request.user
        form.instance.subdivision = self.subdivision
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Продукт "{form.instance.name}" успешно добавлен!'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('subdivision_products', kwargs={
            'subdivision_code': self.object.subdivision.code
        })

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование продукта"""
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Проверяем права перед отображением формы
        self.object = self.get_object()
        
        if not self.object.can_edit(request.user):
            messages.error(request, 'У вас нет прав для редактирования этого продукта')
            return redirect('product_detail',
                          product_id=self.object.id,
                          subdivision_code=self.object.subdivision.code)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Продукт "{form.instance.name}" успешно обновлен!'
        )
        return response
    
    def get_success_url(self):
        return reverse_lazy('product_detail', kwargs={
            'product_id': self.object.id,
            'subdivision_code': self.object.subdivision.code
        })

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление продукта"""
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Проверяем права перед отображением формы
        self.object = self.get_object()
        
        if not self.object.can_delete(request.user):
            messages.error(request, 'У вас нет прав для удаления этого продукта')
            return redirect('product_detail',
                          product_id=self.object.id,
                          subdivision_code=self.object.subdivision.code)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(self.request, 'Продукт успешно удален!')
        return reverse_lazy('subdivision_products', kwargs={
            'subdivision_code': self.object.subdivision.code
        })

    def get_success_url(self):
        messages.success(self.request, 'Продукт успешно удален!')
        return reverse_lazy('subdivision_products', kwargs={
            'subdivision_code': self.object.subdivision.code
        })

@login_required
def upload_product_images(request, product_id):
    """Загрузка нескольких изображений для продукта"""
    product = get_object_or_404(Product, id=product_id)
    
    # Проверка прав
    if not product.can_edit(request.user):
        messages.error(request, 'У вас нет прав для загрузки изображений')
        return redirect('product_detail', 
                       product_id=product.id,
                       subdivision_code=product.subdivision.code)
   
    if request.method == 'POST':
        form = MultipleImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            images = form.cleaned_data['images']
            created_images = []
            
            for image in images:
                # Создаем ProductImage объект
                product_image = ProductImage(
                    product=product,
                    image=image,
                    uploaded_by=request.user
                )
                
                # Если это первое изображение продукта, делаем его основным
                if not product.images.exists():
                    product_image.is_main = True
                
                # Сохраняем - это вызовет метод save() и запустит обработку
                product_image.save()
                created_images.append(product_image)
            
            messages.success(request, f'{len(created_images)} изображений успешно загружены! Обработка запущена.')
            return redirect('product_detail',
                          product_id=product.id,
                          subdivision_code=product.subdivision.code)
    else:
        form = MultipleImageUploadForm()
  
    return render(request, 'catalog/upload_images.html', {
        'form': form,
        'product': product
    })

def search_products(request):
    """Поиск продуктов с учетом регистра для русского и английского языка"""
    query = request.GET.get('q', '').strip()
    
    if query:
        # Приводим запрос к нижнему регистру
        query_lower = query.lower()
        
        # Используем аннотацию с Lower для всех поисковых полей
        products = Product.objects.annotate(
            search_code=Lower('code'),
            search_name=Lower('name'),
            search_description=Lower('description'),
            search_location=Lower('location')
        ).filter(
            Q(search_code__contains=query_lower) |
            Q(search_name__contains=query_lower) |
            Q(search_description__contains=query_lower) |
            Q(search_location__contains=query_lower)
        ).select_related('subdivision').order_by('code')[:50]
    else:
        products = Product.objects.none()
    
    return render(request, 'catalog/search_results.html', {
        'products': products,
        'query': query
    })

@login_required
def user_profile(request):
    """Профиль пользователя"""
    user = request.user
    created_products = Product.objects.filter(created_by=user).count()
    managed_subdivisions = Subdivision.objects.filter(manager=user)
    
    # Получаем группы пользователя
    groups = user.groups.all()
    
    # Получаем названия групп для удобства проверки в шаблоне
    group_names = [group.name for group in groups]
    
    context = {
        'user': user,
        'created_products': created_products,
        'managed_subdivisions': managed_subdivisions,
        'groups': groups,
        'group_names': group_names,  # Добавляем список названий групп
        'is_editor': user.groups.filter(name='Editor').exists(),
        'is_subdivision_admin': user.groups.filter(name='Subdivision_Admin').exists(),
        'is_super_admin': user.groups.filter(name='Super_Admin').exists(),
        'is_viewer': user.groups.filter(name='Viewer').exists(),
    }
    
    return render(request, 'catalog/user_profile.html', context)

class ProductCreateWithImagesView(LoginRequiredMixin, CreateView):
    """Создание продукта с возможностью загрузки изображений"""
    model = Product
    form_class = ProductCreateWithImagesForm
    template_name = 'catalog/product_create_with_images.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Получаем подразделение и сохраняем в атрибуте класса
        self.subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
        
        # Проверяем права
        if not self.subdivision.can_user_add_product(request.user):
            messages.error(
                request, 
                'У вас нет прав для добавления продуктов в это подразделение'
            )
            return redirect('subdivision_products', 
                          subdivision_code=self.subdivision.code)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Устанавливаем подразделение по умолчанию"""
        initial = super().get_initial()
        initial['subdivision'] = self.subdivision
        return initial
    
    def get_form_kwargs(self):
        """Передаем подразделение в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['initial']['subdivision'] = self.subdivision
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Добавляем subdivision в контекст"""
        context = super().get_context_data(**kwargs)
        context['subdivision'] = self.subdivision
        return context
    
    def form_valid(self, form):
        # Проверяем уникальность кода в подразделении
        code = form.cleaned_data.get('code')
        
        # Проверяем, существует ли уже продукт с таким кодом в этом подразделении
        if Product.objects.filter(
            code=code, 
            subdivision=self.subdivision
        ).exists():
            form.add_error(
                'code', 
                f'Продукт с кодом "{code}" уже существует в подразделении "{self.subdivision.name}"'
            )
            return self.form_invalid(form)
        
        # Сохраняем продукт
        form.instance.created_by = self.request.user
        form.instance.subdivision = self.subdivision
        
        # Сначала сохраняем продукт, чтобы получить ID
        self.object = form.save()
        
        # Обрабатываем загруженные изображения из request.FILES
        if 'images' in self.request.FILES:
            images = self.request.FILES.getlist('images')
            if images:
                for image in images:
                    ProductImage.objects.create(
                        product=self.object,
                        image=image,
                        uploaded_by=self.request.user
                    )
                
                messages.success(
                    self.request, 
                    f'Продукт "{form.instance.name}" создан с {len(images)} изображениями!'
                )
            else:
                messages.success(
                    self.request, 
                    f'Продукт "{form.instance.name}" успешно создан!'
                )
        else:
            messages.success(
                self.request, 
                f'Продукт "{form.instance.name}" успешно создан!'
            )
        
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('product_detail', kwargs={
            'product_id': self.object.id,
            'subdivision_code': self.object.subdivision.code
        })

@login_required
@require_POST
@csrf_exempt
def ajax_upload_images(request, product_id):
    """AJAX загрузка изображений"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Проверка прав
        if not product.can_edit(request.user):
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав для загрузки изображений'
            }, status=403)
        
        # Получаем файлы из request.FILES
        files = request.FILES.getlist('files')
        
        if not files:
            return JsonResponse({
                'success': False,
                'error': 'Не выбрано ни одного файла'
            }, status=400)
        
        created_images = []
        for file in files:
            # Проверка размера
            if file.size > 10 * 1024 * 1024:
                continue
            
            # Создаем изображение
            product_image = ProductImage.objects.create(
                product=product,
                image=file,
                uploaded_by=request.user
            )
            
            created_images.append({
                'id': product_image.id,
                'url': product_image.image.url,
                'name': os.path.basename(product_image.image.name)
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Загружено {len(created_images)} изображений',
            'images': created_images
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def quick_product_create(request, subdivision_code):
    """Быстрое создание продукта с минимальными полями"""
    subdivision = get_object_or_404(Subdivision, code=subdivision_code)
    
    # Проверка прав
    if not subdivision.can_user_add_product(request.user):
        messages.error(
            request, 
            'У вас нет прав для добавления продуктов в это подразделение'
        )
        return redirect('subdivision_products', 
                      subdivision_code=subdivision.code)
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            # Проверяем уникальность кода
            code = form.cleaned_data.get('code')
            
            if Product.objects.filter(
                code=code, 
                subdivision=subdivision
            ).exists():
                form.add_error(
                    'code', 
                    f'Продукт с кодом "{code}" уже существует в этом подразделении'
                )
                return render(request, 'catalog/quick_product_create.html', {
                    'form': form,
                    'subdivision': subdivision
                })
            
            product = form.save(commit=False)
            product.created_by = request.user
            product.subdivision = subdivision
            product.save()
            
            messages.success(
                request, 
                f'Продукт "{product.name}" успешно создан!'
            )
            
            # Перенаправляем на страницу загрузки изображений
            return redirect('upload_product_images', product_id=product.id)
    else:
        form = ProductForm(initial={'subdivision': subdivision})
    
    return render(request, 'catalog/quick_product_create.html', {
        'form': form,
        'subdivision': subdivision
    })

@login_required
def check_product_code(request, subdivision_code):
    """Проверка уникальности кода продукта через AJAX"""
    code = request.GET.get('code', '').strip()
    subdivision = get_object_or_404(Subdivision, code=subdivision_code)
    
    if not code:
        return JsonResponse({'valid': False, 'message': 'Код не может быть пустым'})
    
    exists = Product.objects.filter(
        code=code, 
        subdivision=subdivision
    ).exists()
    
    return JsonResponse({
        'valid': not exists,
        'message': 'Код уже используется в этом подразделении' if exists else 'Код доступен'
    })

def custom_logout(request):
    """Кастомный выход из системы с подтверждением"""
    if request.method == 'POST':
        # Выходим из системы
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы')
        # Перенаправляем на страницу подтверждения
        return redirect('logout_confirmation')
    
    # Если GET запрос, показываем форму подтверждения
    return render(request, 'catalog/logout_confirm.html')

def logout_confirmation(request):
    """Страница подтверждения выхода"""
    return render(request, 'catalog/logged_out.html')