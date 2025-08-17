#!/bin/bash

# Script de despliegue para EC2
# Ejecutar como: bash deploy.sh

echo "🚀 Iniciando despliegue en AWS EC2..."

# Actualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3-pip python3-venv nginx postgresql-client git

# Crear directorio del proyecto
sudo mkdir -p /var/www/restaurant_backend
sudo chown $USER:$USER /var/www/restaurant_backend

# Clonar repositorio (reemplazar con tu repo)
cd /var/www/restaurant_backend
git clone https://github.com/TU_USUARIO/restaurant_backend.git .

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements-prod.txt

# Configurar variables de entorno
cat << EOF > .env.prod
DEBUG=False
SECRET_KEY=tu-clave-secreta-super-segura-aqui
ALLOWED_HOSTS=tu-dominio.com,tu-ip-elastica.com

# Base de datos RDS
AWS_DB_NAME=restaurant_db
AWS_DB_USER=postgres
AWS_DB_PASSWORD=tu-password-rds
AWS_DB_HOST=tu-rds-endpoint.amazonaws.com
AWS_DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_STORAGE_BUCKET_NAME=tu-bucket-nombre
AWS_S3_REGION_NAME=us-east-1

# CORS
CORS_ALLOWED_ORIGINS=https://tu-frontend-domain.com

# Email
RESTAURANT_CONTACT_EMAIL=tu-email@dominio.com
EOF

# Migrar base de datos
python manage.py migrate --settings=restaurant_backend.settings_prod

# Recopilar archivos estáticos
python manage.py collectstatic --noinput --settings=restaurant_backend.settings_prod

# Crear superusuario (opcional)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@restaurant.com', 'admin123')" | python manage.py shell --settings=restaurant_backend.settings_prod

echo "✅ Configuración del backend completada!"
