from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    PersonViewSet,
    UserViewSet,
    RoleViewSet,
    PermissionViewSet,
    GlucoseReadingViewSet,
)
 
router = DefaultRouter()
router.register(r'persons',     PersonViewSet,         basename='api-persons')
router.register(r'users',       UserViewSet,           basename='api-users')
router.register(r'roles',       RoleViewSet,           basename='api-roles')
router.register(r'permissions', PermissionViewSet,     basename='api-permissions')
router.register(r'readings',    GlucoseReadingViewSet, basename='api-readings')
 
urlpatterns = [
    path('', include(router.urls)),
]