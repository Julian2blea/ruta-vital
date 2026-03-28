from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

from .models import (
    PerfilUsuario, Encuesta, DatosSalud, HabitosAlimenticios,
    EstiloVida, Sintomas, ResultadoEvaluacion
)
from .serializers import (
    UserSerializer, PerfilUsuarioSerializer, EncuestaSerializer,
    DatosSaludSerializer, HabitosAlimenticiosSerializer,
    EstiloVidaSerializer, SintomasSerializer, ResultadoEvaluacionSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de usuarios.
    
    GET /api/usuarios/ - Listar todos los usuarios
    POST /api/usuarios/ - Crear nuevo usuario
    GET /api/usuarios/{id}/ - Obtener usuario específico
    PUT /api/usuarios/{id}/ - Actualizar usuario completo
    PATCH /api/usuarios/{id}/ - Actualizar usuario parcial
    DELETE /api/usuarios/{id}/ - Eliminar usuario
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['id', 'username', 'date_joined']
    ordering = ['-date_joined']


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de perfiles de usuario.
    
    GET /api/perfiles/ - Listar todos los perfiles
    POST /api/perfiles/ - Crear nuevo perfil
    GET /api/perfiles/{id}/ - Obtener perfil específico
    PUT /api/perfiles/{id}/ - Actualizar perfil completo
    PATCH /api/perfiles/{id}/ - Actualizar perfil parcial
    DELETE /api/perfiles/{id}/ - Eliminar perfil
    """
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usuario']
    ordering_fields = ['id', 'fecha_registro']
    ordering = ['-fecha_registro']


class EncuestaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de encuestas.
    
    GET /api/encuestas/ - Listar todas las encuestas
    POST /api/encuestas/ - Crear nueva encuesta
    GET /api/encuestas/{id}/ - Obtener encuesta específica
    PUT /api/encuestas/{id}/ - Actualizar encuesta completa
    PATCH /api/encuestas/{id}/ - Actualizar encuesta parcial
    DELETE /api/encuestas/{id}/ - Eliminar encuesta
    """
    queryset = Encuesta.objects.all()
    serializer_class = EncuestaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usuario']
    ordering_fields = ['id', 'fecha_creacion']
    ordering = ['-fecha_creacion']
    
    @action(detail=False, methods=['get'])
    def mis_encuestas(self, request):
        """
        Endpoint personalizado para obtener encuestas del usuario actual.
        GET /api/encuestas/mis_encuestas/
        """
        if not request.user.is_authenticated:
            return Response({"detail": "Autenticación requerida."}, status=401)
        
        encuestas = self.queryset.filter(usuario=request.user)
        serializer = self.get_serializer(encuestas, many=True)
        return Response(serializer.data)


class DatosSaludViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de datos de salud.
    
    GET /api/datos-salud/ - Listar todos los datos de salud
    POST /api/datos-salud/ - Crear nuevos datos de salud
    GET /api/datos-salud/{id}/ - Obtener datos de salud específicos
    PUT /api/datos-salud/{id}/ - Actualizar datos de salud completos
    PATCH /api/datos-salud/{id}/ - Actualizar datos de salud parciales
    DELETE /api/datos-salud/{id}/ - Eliminar datos de salud
    """
    queryset = DatosSalud.objects.all()
    serializer_class = DatosSaludSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['encuesta', 'sexo', 'edad']
    search_fields = ['nombre']
    ordering_fields = ['id', 'edad', 'imc']
    ordering = ['-id']


class HabitosAlimenticiosViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de hábitos alimenticios.
    
    GET /api/habitos/ - Listar todos los hábitos
    POST /api/habitos/ - Crear nuevos hábitos
    GET /api/habitos/{id}/ - Obtener hábitos específicos
    PUT /api/habitos/{id}/ - Actualizar hábitos completos
    PATCH /api/habitos/{id}/ - Actualizar hábitos parciales
    DELETE /api/habitos/{id}/ - Eliminar hábitos
    """
    queryset = HabitosAlimenticios.objects.all()
    serializer_class = HabitosAlimenticiosSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['encuesta', 'consume_frutas_verduras', 'desayuna_regularmente']
    ordering_fields = ['id']
    ordering = ['-id']


class EstiloVidaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de estilo de vida.
    
    GET /api/estilo-vida/ - Listar todos los estilos de vida
    POST /api/estilo-vida/ - Crear nuevo estilo de vida
    GET /api/estilo-vida/{id}/ - Obtener estilo de vida específico
    PUT /api/estilo-vida/{id}/ - Actualizar estilo de vida completo
    PATCH /api/estilo-vida/{id}/ - Actualizar estilo de vida parcial
    DELETE /api/estilo-vida/{id}/ - Eliminar estilo de vida
    """
    queryset = EstiloVida.objects.all()
    serializer_class = EstiloVidaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['encuesta', 'ejercicio_regular', 'estres_cronico', 'duerme_bien']
    ordering_fields = ['id']
    ordering = ['-id']


class SintomasViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de síntomas.
    
    GET /api/sintomas/ - Listar todos los síntomas
    POST /api/sintomas/ - Crear nuevos síntomas
    GET /api/sintomas/{id}/ - Obtener síntomas específicos
    PUT /api/sintomas/{id}/ - Actualizar síntomas completos
    PATCH /api/sintomas/{id}/ - Actualizar síntomas parciales
    DELETE /api/sintomas/{id}/ - Eliminar síntomas
    """
    queryset = Sintomas.objects.all()
    serializer_class = SintomasSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['encuesta', 'fatiga_frecuente', 'problemas_digestivos']
    ordering_fields = ['id']
    ordering = ['-id']


class ResultadoEvaluacionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestión de resultados de evaluación.
    
    GET /api/resultados/ - Listar todos los resultados
    POST /api/resultados/ - Crear nuevo resultado
    GET /api/resultados/{id}/ - Obtener resultado específico
    PUT /api/resultados/{id}/ - Actualizar resultado completo
    PATCH /api/resultados/{id}/ - Actualizar resultado parcial
    DELETE /api/resultados/{id}/ - Eliminar resultado
    """
    queryset = ResultadoEvaluacion.objects.all()
    serializer_class = ResultadoEvaluacionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['encuesta', 'nivel_riesgo']
    ordering_fields = ['id', 'puntaje_riesgo']
    ordering = ['-id']