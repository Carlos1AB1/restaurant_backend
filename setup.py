#!/usr/bin/env python
"""
Script para configurar el entorno de desarrollo para Restaurant API.
"""
import os
import sys
import subprocess
import argparse
import secrets
import string


def generate_secret_key(length=50):
    """
    Genera una clave secreta aleatoria.
    """
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_env_file():
    """
    Crea un archivo .env a partir de .env.example si no existe.
    """
    if os.path.exists('.env'):
        print("Archivo .env ya existe. No se sobrescribirá.")
        return

    if not os.path.exists('.env.example'):
        print("ERROR: No se encontró el archivo .env.example")
        return

    with open('.env.example', 'r') as example_file:
        env_content = example_file.read()

    # Reemplazar la clave secreta con una generada
    env_content = env_content.replace('your-secret-key-change-in-production', generate_secret_key())

    with open('.env', 'w') as env_file:
        env_file.write(env_content)

    print("Archivo .env creado.")


def install_dependencies():
    """
    Instala las dependencias del proyecto.
    """
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("Dependencias instaladas correctamente.")
    except subprocess.CalledProcessError:
        print("ERROR: Error al instalar dependencias.")
        return False
    return True


def setup_database():
    """
    Configura la base de datos.
    """
    try:
        # Ejecutar migraciones
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'], check=True)
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("Base de datos configurada correctamente.")
    except subprocess.CalledProcessError:
        print("ERROR: Error al configurar la base de datos.")
        return False
    return True


def create_superuser():
    """
    Crea un superusuario.
    """
    try:
        subprocess.run([sys.executable, 'manage.py', 'createsuperuser'], check=False)
    except subprocess.CalledProcessError:
        print("ERROR: Error al crear superusuario.")
        return False
    return True


def setup_elasticsearch():
    """
    Configura Elasticsearch.
    """
    try:
        # Ejecutar tarea de reindexación
        subprocess.run([sys.executable, 'manage.py', 'shell', '-c',
                        'from search.services import ElasticsearchService; ElasticsearchService.create_index(); ElasticsearchService.reindex_all()'],
                       check=True)
        print("Elasticsearch configurado correctamente.")
    except subprocess.CalledProcessError:
        print("ERROR: Error al configurar Elasticsearch. Asegúrate de que esté instalado y en ejecución.")
        return False
    return True


def collect_static_files():
    """
    Recopila archivos estáticos.
    """
    try:
        subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("Archivos estáticos recopilados correctamente.")
    except subprocess.CalledProcessError:
        print("ERROR: Error al recopilar archivos estáticos.")
        return False
    return True


def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description='Configurar entorno de desarrollo para Restaurant API.')
    parser.add_argument('--all', action='store_true', help='Ejecutar todos los pasos')
    parser.add_argument('--env', action='store_true', help='Crear archivo .env')
    parser.add_argument('--deps', action='store_true', help='Instalar dependencias')
    parser.add_argument('--db', action='store_true', help='Configurar base de datos')
    parser.add_argument('--superuser', action='store_true', help='Crear superusuario')
    parser.add_argument('--es', action='store_true', help='Configurar Elasticsearch')
    parser.add_argument('--static', action='store_true', help='Recopilar archivos estáticos')

    args = parser.parse_args()

    # Si no se especifican argumentos, mostrar ayuda
    if not any(vars(args).values()):
        parser.print_help()
        return

    # Ejecutar pasos según argumentos
    if args.env or args.all:
        create_env_file()

    if args.deps or args.all:
        if not install_dependencies():
            return

    if args.db or args.all:
        if not setup_database():
            return

    if args.superuser or args.all:
        if not create_superuser():
            return

    if args.es or args.all:
        if not setup_elasticsearch():
            return

    if args.static or args.all:
        if not collect_static_files():
            return

    print("\nConfiguración completada.")


if __name__ == '__main__':
    main()