from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.http import JsonResponse, Http404
from .models import Subdivision, Product, ProductImage
from .forms import ProductForm, ProductImageForm, MultipleImageUploadForm
from .decorators import can_edit_product, can_delete_product, can_add_to_subdivision

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
        context['can_add_product'] = self.subdivision.can_add_product(self.request.user)
        
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
    """Создание нового продукта"""
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Проверяем права перед отображением формы
        subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
        
        if not subdivision.can_add_product(request.user):
            messages.error(
                request, 
                'У вас нет прав для добавления продуктов в это подразделение'
            )
            return redirect('subdivision_products', 
                          subdivision_code=subdivision.code)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Устанавливаем подразделение по умолчанию"""
        initial = super().get_initial()
        subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
        initial['subdivision'] = subdivision
        return initial
    
    def get_form_kwargs(self):
        """Передаем подразделение в форму"""
        kwargs = super().get_form_kwargs()
        subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
        kwargs['initial']['subdivision'] = subdivision
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.subdivision = get_object_or_404(
            Subdivision, 
            code=self.kwargs['subdivision_code']
        )
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
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    uploaded_by=request.user
                )
            messages.success(request, f'{len(images)} изображений успешно загружены!')
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
    """Поиск продуктов"""
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        ).select_related('subdivision')[:50]
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
    
    context = {
        'user': user,
        'created_products': created_products,
        'managed_subdivisions': managed_subdivisions,
        'groups': groups,
    }
    
    return render(request, 'catalog/user_profile.html', context)