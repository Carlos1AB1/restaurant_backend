from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at', 'product')
    search_fields = ('comment', 'user__email', 'product__name')
    list_editable = ('is_approved',) # Permitir aprobar/desaprobar desde la lista
    actions = ['approve_reviews', 'unapprove_reviews'] # Acciones masivas

    def approve_reviews(self, request, queryset):
        updated_count = 0
        for review in queryset:
             if not review.is_approved:
                 review.is_approved = True
                 review.save(update_fields=['is_approved', 'updated_at'])
                 # La señal se disparará para cada uno, recalculando el promedio
                 updated_count += 1
        self.message_user(request, f'{updated_count} reseñas fueron aprobadas.')
    approve_reviews.short_description = "Aprobar reseñas seleccionadas"

    def unapprove_reviews(self, request, queryset):
        updated_count = 0
        for review in queryset:
             if review.is_approved:
                 review.is_approved = False
                 review.save(update_fields=['is_approved', 'updated_at'])
                 updated_count += 1
        self.message_user(request, f'{updated_count} reseñas fueron desaprobadas.')
    unapprove_reviews.short_description = "Desaprobar reseñas seleccionadas"

    # Hacer campos no editables directamente en el form si se aprueba/desaprueba con acciones
    # readonly_fields = ('user', 'product', 'created_at', 'updated_at')