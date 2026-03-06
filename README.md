#  Ruta Vital - Predicción de Salud

Plataforma web de predicción de enfermedades basada en análisis de hábitos alimenticios y estilo de vida.

##  Descripción

Ruta Vital es una herramienta de evaluación de salud que permite a los usuarios conocer su riesgo de desarrollar enfermedades crónicas mediante un cuestionario simple de 5 minutos.

##  Características

-  Sistema de autenticación de usuarios
-  Cuestionario interactivo de 4 pasos
-  Predicción de 7 enfermedades comunes
-  Análisis de nivel de riesgo (Bajo, Moderado, Alto)
-  Recomendaciones personalizadas
-  Diseño responsive

## 🛠️ Tecnologías

- **Backend:** Django 5.2.7
- **Base de datos:** MySQL (MariaDB 10.4)
- **Frontend:** HTML5, CSS3, JavaScript
- **Python:** 3.11.7

##  Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/Julian2blea/ruta-vital.git
cd ruta-vital
```

2. Crea un entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Instala dependencias:
```bash
pip install -r requirements.txt
```

4. Configura la base de datos en `settings.py`

5. Ejecuta migraciones:
```bash
python manage.py migrate
```

6. Crea un superusuario:
```bash
python manage.py createsuperuser
```

7. Ejecuta el servidor:
```bash
python manage.py runserver
```

##  Estructura del Proyecto
```
prediccion_enfermedades/
├── config/              # Configuración principal
├── prediccion/          # App principal
│   ├── models.py       # Modelos de datos
│   ├── views.py        # Lógica de vistas
│   ├── forms.py        # Formularios
│   ├── static/         # Archivos estáticos
│   └── templates/      # Templates HTML
├── manage.py
└── requirements.txt
```

##  Autor

Julian Gaitan - Proyecto Integrador

##  Licencia
Este proyecto es parte de un trabajo académico.