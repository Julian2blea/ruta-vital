from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserViewSet, PerfilUsuarioViewSet, EncuestaViewSet,
    DatosSaludViewSet, HabitosAlimenticiosViewSet,
    EstiloVidaViewSet, SintomasViewSet, ResultadoEvaluacionViewSet
)

# Router para registrar los ViewSets
router = DefaultRouter()
router.register(r'usuarios', UserViewSet, basename='api-usuarios')
router.register(r'perfiles', PerfilUsuarioViewSet, basename='api-perfiles')
router.register(r'encuestas', EncuestaViewSet, basename='api-encuestas')
router.register(r'datos-salud', DatosSaludViewSet, basename='api-datos-salud')
router.register(r'habitos', HabitosAlimenticiosViewSet, basename='api-habitos')
router.register(r'estilo-vida', EstiloVidaViewSet, basename='api-estilo-vida')
router.register(r'sintomas', SintomasViewSet, basename='api-sintomas')
router.register(r'resultados', ResultadoEvaluacionViewSet, basename='api-resultados')

urlpatterns = [
    path('', include(router.urls)),
]