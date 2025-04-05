from rest_framework import serializers
from .models import Category, Dish, Ingredient, DishIngredient, Promotion, Review


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Ingredient."""

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'description', 'is_allergen']


class DishIngredientSerializer(serializers.ModelSerializer):
    """Serializer para el modelo DishIngredient."""

    ingredient_details = IngredientSerializer(source='ingredient', read_only=True)

    class Meta:
        model = DishIngredient
        fields = ['id', 'ingredient', 'ingredient_details', 'quantity', 'is_optional', 'extra_price']
        extra_kwargs = {
            'ingredient': {'write_only': True}
        }


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Review."""

    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'user_username', 'created_at']
        read_only_fields = ['created_at', 'user_username']

    def create(self, validated_data):
        # Asignar el usuario actual como autor
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PromotionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Promotion."""

    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'start_date', 'end_date', 'is_active', 'is_valid'
        ]
        read_only_fields = ['is_valid']


class DishListSerializer(serializers.ModelSerializer):
    """Serializer para listar platos."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    final_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    has_promotion = serializers.BooleanField(read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'price', 'final_price', 'has_promotion',
            'image', 'category', 'category_name', 'is_featured', 'preparation_time',
            'calories', 'average_rating'
        ]

    def get_average_rating(self, obj):
        """Calcula la calificación promedio del plato."""
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)


class DishDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de platos."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    ingredients = DishIngredientSerializer(many=True, read_only=True)
    active_promotion = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    final_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'price', 'final_price', 'image',
            'category', 'category_name', 'is_featured', 'preparation_time',
            'calories', 'ingredients', 'active_promotion', 'reviews', 'average_rating'
        ]

    def get_active_promotion(self, obj):
        """Retorna la promoción activa para el plato si existe."""
        promotion = obj.promotions.filter(
            is_active=True,
            start_date__lte=serializers.DateTimeField().to_representation(serializers.DateTimeField().to_internal_value(
                serializers.DateTimeField().to_representation(serializers.DateTimeField().to_internal_value('now')))),
            end_date__gte=serializers.DateTimeField().to_representation(serializers.DateTimeField().to_internal_value(
                serializers.DateTimeField().to_representation(serializers.DateTimeField().to_internal_value('now'))))
        ).first()

        if promotion:
            return PromotionSerializer(promotion).data
        return None

    def get_average_rating(self, obj):
        """Calcula la calificación promedio del plato."""
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)


class DishCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear o actualizar platos."""

    ingredients = DishIngredientSerializer(many=True, required=False)

    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'price', 'image', 'category',
            'is_featured', 'is_active', 'preparation_time', 'calories', 'ingredients'
        ]

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        dish = Dish.objects.create(**validated_data)

        # Crear ingredientes asociados
        self._create_or_update_ingredients(dish, ingredients_data)

        return dish

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        # Actualizar campos del plato
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar ingredientes si se proporcionaron
        if ingredients_data is not None:
            # Eliminar ingredientes anteriores
            instance.ingredients.all().delete()
            # Crear nuevos ingredientes
            self._create_or_update_ingredients(instance, ingredients_data)

        return instance

    def _create_or_update_ingredients(self, dish, ingredients_data):
        """Helper para crear o actualizar ingredientes de un plato."""
        for ingredient_data in ingredients_data:
            DishIngredient.objects.create(dish=dish, **ingredient_data)


class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer para listar categorías."""

    dish_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'order', 'dish_count']


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de categorías."""

    dishes = DishListSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'order', 'dishes']


class PromotionDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de promociones."""

    dishes = DishListSerializer(many=True, read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'start_date', 'end_date', 'is_active', 'dishes', 'is_valid'
        ]
        read_only_fields = ['is_valid']