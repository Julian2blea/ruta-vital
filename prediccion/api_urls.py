from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    PersonViewSet,
    UserViewSet,
    RoleViewSet,
    PermissionViewSet,
    GlucoseReadingViewSet,
    UserHasRoleViewSet,
)
from .auth_views import api_login, api_register, api_logout

router = DefaultRouter()
router.register(r'persons',     PersonViewSet,         basename='api-persons')
router.register(r'users',       UserViewSet,           basename='api-users')
router.register(r'roles',       RoleViewSet,           basename='api-roles')
router.register(r'permissions', PermissionViewSet,     basename='api-permissions')
router.register(r'readings',    GlucoseReadingViewSet, basename='api-readings')
router.register(r'user-roles', UserHasRoleViewSet,    basename='api-user-roles')

urlpatterns = [
    # ── Auth endpoints ────────────────────────────────────────
    path('auth/login/',    api_login,    name='api-login'),
    path('auth/register/', api_register, name='api-register'),
    path('auth/logout/',   api_logout,   name='api-logout'),

    # ── REST ViewSets ─────────────────────────────────────────
    path('', include(router.urls)),
]