from django.core.mail import send_mail
from django.conf import settings

print('=== CONFIGURACIÓN DE EMAIL ===')
print(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
print(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
print(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')

print('\n=== ENVIANDO EMAIL DE PRUEBA ===')
try:
    result = send_mail(
        subject='🍽️ Test Email - Restaurante',
        message='Este es un email de prueba para verificar la configuración SMTP del restaurante.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['Archudeluxe2@gmail.com'],
        fail_silently=False,
    )
    print(f'✅ Email enviado exitosamente! Resultado: {result}')
except Exception as e:
    print(f'❌ Error al enviar email: {e}')
    import traceback
    traceback.print_exc()
