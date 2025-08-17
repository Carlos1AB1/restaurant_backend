from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'slug', 'image_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)} # Autocompleta slug basado en name
    list_editable = ('order', 'is_active')  # Permitir editar orden directamente en la lista
    list_display_links = ('name',)  # El enlace será el nombre, no el orden
    fields = ('order', 'name', 'slug', 'description', 'image', 'is_active')
    ordering = ('order', 'name')  # Ordenar por orden en el admin también
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'image_preview', 'is_available', 'average_rating', 'created_at')
    list_filter = ('is_available', 'category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'is_available') # Permite editar estos campos en la lista
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('average_rating',) # La calificación promedio no se edita manualmente
    fields = ('category', 'name', 'slug', 'description', 'price', 'image', 'is_available')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "Sin imagen"
    image_preview.short_description = 'Vista previa'