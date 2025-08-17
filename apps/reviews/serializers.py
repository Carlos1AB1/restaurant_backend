from rest_framework import serializers
from .models import Review
from apps.users.serializers import UserSerializer # Para mostrar info del usuario

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True) # Mostrar detalles del usuario que hizo la reseña
    # Opcional: Mostrar solo el nombre de usuario
    # user = serializers.StringRelatedField(read_only=True)
    product_slug = serializers.SlugRelatedField(slug_field='slug', source='product', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'product_slug', 'user', 'rating', 'comment', 'is_approved', 'created_at']
        read_only_fields = ['id', 'user', 'is_approved', 'created_at', 'product_slug']
        # 'product' será write_only para la creación, se leerá via product_slug
        extra_kwargs = {
            'product': {'write_only': True, 'required': True}
        }


    def validate(self, data):
        # Validar que el usuario no haya reseñado ya este producto
        request = self.context.get('request')
        user = request.user
        product = data.get('product')

        # Solo validar en creación (instance is None)
        if not self.instance and Review.objects.filter(product=product, user=user).exists():
             raise serializers.ValidationError("Ya has dejado una reseña para este producto.")

        # Opcional (más avanzado): Validar que el usuario haya comprado el producto
        # if not OrderItem.objects.filter(order__user=user, product=product, order__status='DELIVERED').exists():
        #     raise serializers.ValidationError("Solo puedes reseñar productos que hayas comprado y recibido.")

        return data

    def create(self, validated_data):
         # Asignar el usuario autenticado automáticamente
         validated_data['user'] = self.context['request'].user
         # Las reseñas nuevas no están aprobadas por defecto
         validated_data['is_approved'] = False
         review = Review.objects.create(**validated_data)
         # La señal post_save se encargará de actualizar el promedio si se aprueba después
         return review