from rest_framework import serializers
from .models import Category, Product
from apps.reviews.serializers import ReviewSerializer # Para anidar reseñas

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active', 'order']
        read_only_fields = ['slug'] # El slug se genera automáticamente


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField() # Muestra el nombre de la categoría
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, label="Categoría"
    )
    # reviews = ReviewSerializer(many=True, read_only=True) # Opcional: Anidar reseñas aprobadas
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_id', 'name', 'slug', 'description',
            'price', 'image', 'is_available', 'average_rating', #'reviews',
            'review_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'average_rating', 'review_count', 'created_at', 'updated_at']

    def get_review_count(self, obj):
        # Contar solo reseñas aprobadas
        return obj.reviews.filter(is_approved=True).count()

    # Opcional: Validar que el precio sea positivo
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser un valor positivo.")
        return value