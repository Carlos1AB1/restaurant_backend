from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Avg # Para calcular el promedio de calificación

# Función para definir la ruta de subida de imágenes de categorías
def category_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/category_images/<category_slug>/<filename>
    return f'category_images/{instance.slug}/{filename}'

# Función para definir la ruta de subida de imágenes de productos
def product_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/product_images/<product_id>/<filename>
    return f'product_images/{instance.slug}/{filename}'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=110, unique=True, blank=True, help_text="Versión amigable para URL (se genera automáticamente si se deja en blanco)")
    description = models.TextField(blank=True, verbose_name="Descripción")
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True, verbose_name="Imagen de Categoría", help_text="Imagen representativa de la categoría")
    is_active = models.BooleanField(default=True, verbose_name="Activa", help_text="Marcar si la categoría está activa")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden", help_text="Orden de aparición (menor número aparece primero)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['order', 'name']  # Ordenar por campo order primero, luego por nombre

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name="Categoría")
    name = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text="Versión amigable para URL (se genera automáticamente si se deja en blanco)")
    description = models.TextField(verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name="Precio")
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True, verbose_name="Imagen")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campo para calificación promedio (calculado)
    average_rating = models.FloatField(default=0.0, editable=False, verbose_name="Calificación Promedio")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Asegurar slug único
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def update_average_rating(self):
        """Calcula y actualiza la calificación promedio del producto."""
        # Importación local para evitar dependencia circular
        from apps.reviews.models import Review
        avg = Review.objects.filter(product=self, is_approved=True).aggregate(Avg('rating'))['rating__avg']
        self.average_rating = avg if avg is not None else 0.0
        self.save(update_fields=['average_rating']) # Guardar solo este campo para eficiencia