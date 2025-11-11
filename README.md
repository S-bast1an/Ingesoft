# SabidurIA

Plataforma educativa para ayudar a estudiantes en matemáticas de bachillerato y secundaria.

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd sabiduria
```

2. Crear un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
```

3. Activar el entorno virtual:
- En Windows:
```bash
venv\Scripts\activate
```
- En macOS/Linux:
```bash
source venv/bin/activate
```

4. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

## Configuración inicial

1. Inicializar la base de datos y crear usuario de prueba:
```bash
python init_db.py
```

## Ejecutar la aplicación

1. Iniciar el servidor de desarrollo:
```bash
python app.py
```

2. Abrir el navegador y visitar:
```
http://localhost:5000
```

## Credenciales de prueba

- Número de Tarjeta de Identidad: 1234567890
- Contraseña: password123

## Características

- Sistema de login con número de tarjeta de identidad
- Dashboard personalizado
- Secciones de matemáticas nivel primaria y nivel secundaria
- Seguimiento de progreso
- Interfaz moderna y responsiva

## Tecnologías utilizadas

- Flask (Framework web)
- SQLAlchemy (ORM)
- Bootstrap 5 (Framework CSS)
- SQLite (Base de datos) 