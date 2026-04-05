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
    """
    GET    /api/persons/        - List all persons
    POST   /api/persons/        - Create a person
    GET    /api/persons/{id}/   - Retrieve a person
    PUT    /api/persons/{id}/   - Full update
    PATCH  /api/persons/{id}/   - Partial update
    DELETE /api/persons/{id}/   - Delete
    """
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
    """
    GET    /api/users/          - List all users
    POST   /api/users/          - Create a user
    GET    /api/users/{id}/     - Retrieve a user
    PUT    /api/users/{id}/     - Full update
    PATCH  /api/users/{id}/     - Partial update
    DELETE /api/users/{id}/     - Delete
 
    GET    /api/users/me/       - Current authenticated user
    """
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
        """Returns the currently authenticated user."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
 
 
# ─────────────────────────────────────────────
# ROLE
# ─────────────────────────────────────────────
 
class RoleViewSet(viewsets.ModelViewSet):
    """
    GET    /api/roles/          - List all roles
    POST   /api/roles/          - Create a role
    GET    /api/roles/{id}/     - Retrieve a role
    PUT    /api/roles/{id}/     - Full update
    PATCH  /api/roles/{id}/     - Partial update
    DELETE /api/roles/{id}/     - Delete
    """
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
    """
    GET    /api/permissions/        - List all permissions
    POST   /api/permissions/        - Create a permission
    GET    /api/permissions/{id}/   - Retrieve a permission
    PUT    /api/permissions/{id}/   - Full update
    PATCH  /api/permissions/{id}/   - Partial update
    DELETE /api/permissions/{id}/   - Delete
    """
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
    """
    GET    /api/readings/               - List readings of current user
    POST   /api/readings/               - Register a new reading (auto-generates recommendation)
    GET    /api/readings/{id}/          - Retrieve a reading with its recommendation
    DELETE /api/readings/{id}/          - Delete a reading
 
    GET    /api/readings/history/       - Lightweight list for charts/history
    GET    /api/readings/my_readings/   - Alias for filtered list
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'context', 'source']
    ordering_fields = ['id', 'reading_date', 'glucose_value']
    ordering = ['-reading_date']
 
    def get_queryset(self):
        """Each user only sees their own readings."""
        return GlucoseReading.objects.filter(
            user=self.request.user
        ).select_related('recommendation')
 
    def get_serializer_class(self):
        if self.action == 'create':
            return GlucoseReadingCreateSerializer
        if self.action == 'history':
            return GlucoseHistorySerializer
        return GlucoseReadingSerializer
 
    def perform_create(self, serializer):
        """Save the reading and auto-generate its recommendation."""
        reading = serializer.save(user=self.request.user)
        rec_data = build_recommendation(reading)
        GlucoseRecommendation.objects.create(reading=reading, **rec_data)
 
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Lightweight endpoint for the chart / history screen.
        GET /api/readings/history/
        """
        readings = self.get_queryset()
        serializer = GlucoseHistorySerializer(readings, many=True)
        return Response(serializer.data)
 
    @action(detail=False, methods=['get'])
    def my_readings(self, request):
        """
        Full reading list with recommendations for the current user.
        GET /api/readings/my_readings/
        """
        readings = self.get_queryset()
        serializer = GlucoseReadingSerializer(readings, many=True)
        return Response(serializer.data)
 