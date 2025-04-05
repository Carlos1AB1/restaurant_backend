from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """
    Modelo para categorías de platos en el menú.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(_('nombre'), max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    image = models.ImageField(
        _('imagen'),
        upload_to='categories/',
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(
        _('orden'),
        default=0,
        help_text=_('Orden de aparición en la lista de categorías')
    )
    is_active = models.BooleanField(_('activo'), default=True)
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('categoría')
        verbose_name_plural = _('categorías')
        ordering = ['order']

    def __str__(self):
        return self.name

    @property
    def dish_count(self):
        """Retorna el número de platos activos en esta categoría."""
        return self.dishes.filter(is_active=True).count()


class Dish(models.Model):
    """
    Modelo para platos del menú.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(_('nombre'), max_length=200)
    description = models.TextField(_('descripción'))
    price = models.DecimalField(
        _('precio'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        _('imagen'),
        upload_to='dishes/',
        blank=True,
        null=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name=_('categoría')
    )
    is_featured = models.BooleanField(_('destacado'), default=False)
    is_active = models.BooleanField(_('activo'), default=True)
    preparation_time = models.PositiveIntegerField(
        _('tiempo de preparación (min)'),
        default=15,
        help_text=_('Tiempo estimado de preparación en minutos')
    )
    calories = models.PositiveIntegerField(
        _('calorías'),
        null=True,
        blank=True,
        help_text=_('Cantidad de calorías por porción')
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('plato')
        verbose_name_plural = _('platos')
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        """
        Retorna el precio final con promociones aplicadas si existen.
        """
        active_promotion = self.promotions.filter(
            is_active=True,
            start_date__lte=models.functions.Now(),
            end_date__gte=models.functions.Now()
        ).first()

        if active_promotion:
            if active_promotion.discount_type == 'PERCENTAGE':
                return self.price * (1 - active_promotion.discount_value / 100)
            elif active_promotion.discount_type == 'FIXED':
                return max(self.price - active_promotion.discount_value, 0)

        return self.price

    @property
    def has_promotion(self):
        """
        Retorna True si el plato tiene una promoción activa.
        """
        return self.promotions.filter(
            is_active=True,
            start_date__lte=models.functions.Now(),
            end_date__gte=models.functions.Now()
        ).exists()


class Ingredient(models.Model):
    """
    Modelo para ingredientes de platos.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(_('nombre'), max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    is_allergen = models.BooleanField(_('alérgeno'), default=False)
    is_active = models.BooleanField(_('activo'), default=True)

    class Meta:
        verbose_name = _('ingrediente')
        verbose_name_plural = _('ingredientes')
        ordering = ['name']

    def __str__(self):
        return self.name


class DishIngredient(models.Model):
    """
    Modelo para relación entre platos e ingredientes.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name=_('plato')
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='dishes',
        verbose_name=_('ingrediente')
    )
    quantity = models.CharField(
        _('cantidad'),
        max_length=50,
        blank=True,
        help_text=_('Ej: 100g, 2 cucharadas, etc.')
    )
    is_optional = models.BooleanField(_('opcional'), default=False)
    extra_price = models.DecimalField(
        _('precio extra'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = _('ingrediente del plato')
        verbose_name_plural = _('ingredientes del plato')
        unique_together = ['dish', 'ingredient']

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name}"


class Promotion(models.Model):
    """
    Modelo para promociones de platos.
    """
    DISCOUNT_TYPES = (
        ('PERCENTAGE', _('Porcentaje')),
        ('FIXED', _('Monto fijo')),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(_('nombre'), max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    discount_type = models.CharField(
        _('tipo de descuento'),
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='PERCENTAGE'
    )
    discount_value = models.DecimalField(
        _('valor del descuento'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    start_date = models.DateTimeField(_('fecha de inicio'))
    end_date = models.DateTimeField(_('fecha de fin'))
    is_active = models.BooleanField(_('activo'), default=True)
    dishes = models.ManyToManyField(
        Dish,
        related_name='promotions',
        verbose_name=_('platos'),
        blank=True
    )
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('promoción')
        verbose_name_plural = _('promociones')
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def is_valid(self):
        """
        Retorna True si la promoción está activa y dentro del período válido.
        """
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now and self.end_date >= now


class Review(models.Model):
    """
    Modelo para reseñas de platos.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('plato')
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('usuario')
    )
    rating = models.IntegerField(
        _('calificación'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_('comentario'), blank=True)
    created_at = models.DateTimeField(_('creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('actualizado el'), auto_now=True)

    class Meta:
        verbose_name = _('reseña')
        verbose_name_plural = _('reseñas')
        ordering = ['-created_at']
        unique_together = ['dish', 'user']

    def __str__(self):
        return f"{self.dish.name} - {self.user.username} - {self.rating}/5"