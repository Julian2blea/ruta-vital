from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenRefreshView

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

    # API REST (ViewSets + auth endpoints custom)
    path('api/', include('prediccion.api_urls')),

    # Endpoint estándar de refresh — el frontend lo llama directamente
    # POST /api/token/refresh/  { refresh }  →  { access, refresh (rotado) }
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Vistas web Django 
    path('', include('prediccion.urls')),
]