#  Ruta Vital - Backend API

API REST desarrollada con Django y Django REST Framework para la gestión de usuarios, lecturas de glucosa y predicción de riesgos de salud basada en hábitos alimenticios.

---

##  Descripción

Ruta Vital es un sistema integral orientado al monitoreo de salud, que permite:

- Registrar lecturas de glucosa
- Analizar resultados según estándares clínicos (ADA)
- Generar recomendaciones automáticas
- Gestionar usuarios, roles y permisos
- Proveer datos a una aplicación móvil desarrollada en Expo

---

##  Características principales

###  Autenticación
- Registro e inicio de sesión
- Manejo de tokens
- Endpoint `/api/users/me/`

###  Lecturas de glucosa
- Registro de lecturas (manual o simuladas)
- Clasificación automática:
  - Hipoglucemia
  - Normal
  - Prediabetes
  - Glucosa alta
- Recomendaciones personalizadas
- Historial de lecturas

###  Análisis
- Datos optimizados para gráficas
- Seguimiento de evolución del usuario

###  Panel de administración
- Gestión de usuarios
- Asignación de roles (admin / paciente)
- Visualización de permisos
- Acceso a todas las lecturas del sistema

###  Lógica inteligente
- Generación automática de recomendaciones
- Evaluación basada en estándares ADA

---

##  Tecnologías

- **Backend:** Django 5 + Django REST Framework
- **Base de datos:** MySQL / MariaDB
- **Autenticación:** Token Authentication
- **Servidor:** Gunicorn (producción)
- **Despliegue:** Microsoft Azure
- **Lenguaje:** Python 3.11

---

##  API Endpoints principales

###  Auth
- POST /api/auth/login/
- POST /api/auth/register/
- POST /api/auth/logout/
- GET /api/users/me/

---

### Usuarios
- GET /api/users/

---  

### Roles y Permisos
- GET /api/roles/
- GET /api/permissions/
- POST /api/user-roles/ ← asignación de roles

---
  
### Lecturas
- POST /api/readings/
- GET /api/readings/
- GET /api/readings/history/
- GET /api/readings/my_readings/

---

##  Instalación local

  1. Clonar repositorio:
      ```bash
      git clone https://github.com/Julian2blea/ruta-vital-movil.git
      cd ruta-vital-movil
  
  2. Crear entorno virtual:
      ```bash
      python -m venv venv
      venv\Scripts\activate
    
  3. Instalar dependencias:
      ```bash
      pip install -r requirements.txt

  4. Configurar base de datos en settings.py
  
  5. Ejecutar migraciones:
      ```bash
      python manage.py migrate
  
  6. Crear superusuario:
      ```bash
      python manage.py createsuperuser
  
  7. Ejecutar servidor:
      ```bash
      python manage.py runserver

---

### Despliegue (Azure)

  El proyecto está preparado para despliegue en Azure mediante:
  - Procfile
  - gunicorn
  - whitenoise
  
  Comando de inicio:
    ```bash
    web: gunicorn config.wsgi

---

### Estructura del proyecto:
prediccion_enfermedades/
├── config/                 # Configuración principal (settings, urls, wsgi)
├── prediccion/             # App principal
│   ├── models.py
│   ├── serializers.py
│   ├── api_views.py        # API REST endpoints
│   ├── views.py            # Lógica de recomendaciones
├── manage.py
├── requirements.txt
├── Procfile

---

### Roles del sistema

- Admin:	Acceso total, gestión de usuarios y datos
- Usuario comun:	Registro y consulta de sus lecturas

---

### Integracion
Este backend se conecta con una aplicación móvil desarrollada en Expo (React Native), la cual consume esta API.

---

### Autores
Proyecto integrador
Julian Gaitan, Albeiro Jimenez - Ingeniería de Software
Proyecto academico con fines educativos
