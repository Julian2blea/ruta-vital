from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
 
from .models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission,
    GlucoseReading, GlucoseRecommendation,
)
from .serializers import (
    PersonSerializer,
    UserSerializer, UserCreateSerializer,
    RoleSerializer, PermissionSerializer,
    GlucoseReadingSerializer, GlucoseReadingCreateSerializer,
    GlucoseHistorySerializer, GlucoseRecommendationSerializer,
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

            UserHasRole.objects.create(user=user, role=role)

            return Response({"message": "Rol asignado correctamente"}, status=201)

        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        except Role.DoesNotExist:
            return Response({"error": "Rol no encontrado"}, status=404)    