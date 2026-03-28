from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Ruta Vital API",
        default_version='v1',
        description="API REST para la plataforma de predicción de enfermedades Ruta Vital",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contacto@rutavital.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('prediccion.urls')), 
    path('api/', include('prediccion.api_urls')),  
    
    # Documentación Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]