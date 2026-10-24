from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.decorators import api_view as drf_api_view, permission_classes as drf_permission_classes
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone as tz
 
from .models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission,
    GlucoseReading, GlucoseRecommendation,
    IoTDevice, TelemetryLog
)
from .serializers import (
    PersonSerializer,
    UserSerializer, UserCreateSerializer,
    RoleSerializer, PermissionSerializer,
    GlucoseReadingSerializer, GlucoseReadingCreateSerializer,
    GlucoseHistorySerializer, GlucoseRecommendationSerializer,
    IoTDeviceSerializer, TelemetryLogSerializer, TelemetryIngestSerializer
)
from .views import build_recommendation
 
 
# ─────────────────────────────────────────────
# PERSON
# ─────────────────────────────────────────────
 
class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['id', 'last_name']
    ordering = ['last_name']
 
 
# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
 
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('person').prefetch_related('roles')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['login', 'person__first_name', 'person__last_name']
    ordering_fields = ['id', 'date_joined']
    ordering = ['-date_joined']
 
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
 
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
 
 
# ─────────────────────────────────────────────
# ROLE
# ─────────────────────────────────────────────
 
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related('permissions')
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['id', 'description']
    ordering = ['description']
 
 
# ─────────────────────────────────────────────
# PERMISSION
# ─────────────────────────────────────────────
 
class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['id', 'description']
    ordering = ['description']
 
 
# ─────────────────────────────────────────────
# GLUCOSE READING
# ─────────────────────────────────────────────
 
class GlucoseReadingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'context', 'source']
    ordering_fields = ['id', 'reading_date', 'glucose_value']
    ordering = ['-reading_date']
 
    def _is_admin(self, request):
        """Returns True if the current user is staff or has the 'admin' role."""
        return (
            request.user.is_staff or
            request.user.roles.filter(description='admin').exists()
        )
 
    def get_queryset(self):
        """
        Admins see ALL readings from all users (with user info).
        Regular users only see their own readings.
        """
        if self._is_admin(self.request):
            return GlucoseReading.objects.all().select_related(
                'recommendation', 'user', 'user__person'
            ).order_by('-reading_date')
        return GlucoseReading.objects.filter(
            user=self.request.user
        ).select_related('recommendation').order_by('-reading_date')
 
    def get_serializer_class(self):
        if self.action == 'create':
            return GlucoseReadingCreateSerializer
        if self.action == 'history':
            return GlucoseHistorySerializer
        return GlucoseReadingSerializer
 
    def create(self, request, *args, **kwargs):
        """Override create to return full reading with id + recommendation."""
        create_serializer = GlucoseReadingCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
 
        reading = create_serializer.save(user=request.user)
 
        rec_data = build_recommendation(reading)
        GlucoseRecommendation.objects.create(reading=reading, **rec_data)
 
        reading.refresh_from_db()
        full_serializer = GlucoseReadingSerializer(
            reading,
            context={'request': request}
        )
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)
 
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Lightweight list for charts and history screen.
        Regular users: own readings only.
        Admins: all readings.
        GET /api/readings/history/
        """
        readings = self.get_queryset()
        serializer = GlucoseHistorySerializer(readings, many=True)
        return Response(serializer.data)
 
    @action(detail=False, methods=['get'])
    def my_readings(self, request):
        """
        Full reading list with nested recommendations.
        Regular users: own readings only.
        Admins: ALL readings from every user.
        GET /api/readings/my_readings/
        """
        readings = self.get_queryset()
        serializer = GlucoseReadingSerializer(readings, many=True)
        return Response(serializer.data)

# ─────────────────────────────────────────────
# USER HAS ROLE (Asignación de roles)
# ─────────────────────────────────────────────

class UserHasRoleViewSet(viewsets.ModelViewSet):
    queryset = UserHasRole.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user')
        role_id = request.data.get('role')

        try:
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)

            
            obj, created = UserHasRole.objects.get_or_create(user=user, role=role)

            if not created:
                return Response(
                    {"message": "El usuario ya tiene ese rol"},
                    status=status.HTTP_200_OK
                )

            return Response({"message": "Rol asignado correctamente"}, status=201)

        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)
        except Role.DoesNotExist:
            return Response({"error": "Rol no encontrado"}, status=404)

@drf_api_view(['GET'])
@drf_permission_classes([DRFIsAuthenticated])
def predict_risk(request):
    """
    GET /api/predictions/risk/
    Retorna el nivel de riesgo glucémico del usuario autenticado
    basado en sus últimas 10 lecturas usando el modelo de ML.
    """
    try:
        from prediccion.ml.predict import predict_user_risk
        result = predict_user_risk(request.user)
        return Response(result, status=status.HTTP_200_OK)
    except FileNotFoundError:
        return Response(
            {'error': 'Modelo de IA no disponible. Contacta al administrador.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        return Response(
            {'error': f'Error en predicción: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@drf_api_view(['GET'])
@drf_permission_classes([DRFIsAuthenticated])
def all_users_risk(request):
    """
    GET /api/predictions/all-risks/
    Solo para admins — retorna riesgo de todos los pacientes.
    """
    from prediccion.ml.predict import predict_user_risk

    if not (request.user.is_staff or
            request.user.roles.filter(description='admin').exists()):
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)

    try:
        users   = User.objects.filter(is_staff=False).prefetch_related('readings', 'person')
        results = []
        for user in users:
            risk = predict_user_risk(user)
            results.append({
                'user_id':   user.id,
                'login':     user.login,
                'name':      f"{user.person.first_name} {user.person.last_name}" if user.person else user.login,
                **risk,
            })
        results.sort(key=lambda x: (x['risk_level'] or -1), reverse=True)
        return Response(results, status=status.HTTP_200_OK)
    except FileNotFoundError:
        return Response(
            {'error': 'Modelo de IA no disponible.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class IoTDeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD de dispositivos IoT.
    Admin ve todos los dispositivos.
    Usuario normal ve solo los suyos.
    """
    serializer_class   = IoTDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self._is_admin(self.request):
            return IoTDevice.objects.all().select_related('user', 'user__person')
        return IoTDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_devices(self, request):
        """GET /api/iot/devices/my_devices/ — dispositivos del usuario autenticado."""
        devices = IoTDevice.objects.filter(user=request.user)
        return Response(IoTDeviceSerializer(devices, many=True).data)

    @action(detail=True, methods=['post'])
    def ping(self, request, pk=None):
        """POST /api/iot/devices/{id}/ping/ — actualiza last_ping del dispositivo."""
        device = self.get_object()
        device.last_ping = tz.now()
        device.status    = 'active'
        device.save(update_fields=['last_ping', 'status'])
        return Response({'message': 'Ping registrado', 'last_ping': device.last_ping})


@drf_api_view(['POST'])
@drf_permission_classes([permissions.IsAuthenticated])
def telemetry_ingest(request):
    """
    POST /api/telemetry/ingest/

    Endpoint principal de telemetría IoT.
    Simula la recepción de datos desde un glucómetro conectado.
    """
    serializer = TelemetryIngestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # 1. Buscar o registrar el dispositivo
    device, created = IoTDevice.objects.get_or_create(
        device_id=data['device_id'],
        defaults={
            'user':        request.user,
            'device_name': f"Glucómetro {data['device_id']}",
            'status':      'active',
        }
    )
    device.last_ping = tz.now()
    device.status    = 'active'
    device.save(update_fields=['last_ping', 'status'])

    # 2. Crear lectura glucémica con source='device'
    from .serializers import GlucoseReadingCreateSerializer, GlucoseReadingSerializer
    reading_data = {
        'glucose_value': data['glucose_value'],
        'context':       data['context'],
        'source':        'device',
        'notes':         data.get('notes', f'Telemetría automática — Dispositivo {data["device_id"]}'),
    }
    reading_serializer = GlucoseReadingCreateSerializer(data=reading_data)
    reading_serializer.is_valid(raise_exception=True)
    reading = reading_serializer.save(user=request.user)

    # 3. Generar recomendación
    rec_data = build_recommendation(reading)
    GlucoseRecommendation.objects.create(reading=reading, **rec_data)
    reading.refresh_from_db()

    # 4. Registrar log de telemetría
    ip = request.META.get('REMOTE_ADDR')
    TelemetryLog.objects.create(
        device      = device,
        reading     = reading,
        raw_payload = {
            'device_id':     data['device_id'],
            'glucose_value': data['glucose_value'],
            'context':       data['context'],
            'timestamp':     str(tz.now()),
        },
        ip_address = ip,
        signal_ok  = True,
    )

    # 5. Predicción de riesgo IA opcional
    risk_data = None
    try:
        from prediccion.ml.predict import predict_user_risk
        risk_data = predict_user_risk(request.user)
    except Exception:
        pass

    full_serializer = GlucoseReadingSerializer(reading, context={'request': request})
    return Response({
        'reading':      full_serializer.data,
        'device':       IoTDeviceSerializer(device).data,
        'device_new':   created,
        'risk':         risk_data,
    }, status=status.HTTP_201_CREATED)


@drf_api_view(['GET'])
@drf_permission_classes([permissions.IsAuthenticated])
def telemetry_status(request):
    """
    GET /api/telemetry/status/
    Estado del sistema IoT para el usuario autenticado.
    """
    devices = IoTDevice.objects.filter(user=request.user)
    logs    = TelemetryLog.objects.filter(
        device__user=request.user
    ).order_by('-received_at')[:5]

    return Response({
        'total_devices':  devices.count(),
        'active_devices': devices.filter(status='active').count(),
        'devices':        IoTDeviceSerializer(devices, many=True).data,
        'recent_logs':    TelemetryLogSerializer(logs, many=True).data,
    })


@drf_api_view(['GET'])
@drf_permission_classes([permissions.IsAuthenticated])
def telemetry_dashboard(request):
    """
    GET /api/telemetry/dashboard/
    Solo admin — estadísticas globales de telemetría IoT.
    """
    if not (request.user.is_staff or
            request.user.roles.filter(description='admin').exists()):
        return Response({'error': 'Acceso denegado'}, status=status.HTTP_403_FORBIDDEN)

    from django.db.models import Count
    total_devices = IoTDevice.objects.count()
    active        = IoTDevice.objects.filter(status='active').count()
    total_logs    = TelemetryLog.objects.count()
    recent_logs   = TelemetryLog.objects.select_related(
        'device', 'device__user', 'reading'
    ).order_by('-received_at')[:20]

    return Response({
        'total_devices':  total_devices,
        'active_devices': active,
        'total_telemetry_logs': total_logs,
        'recent_logs':    TelemetryLogSerializer(recent_logs, many=True).data,
    })   