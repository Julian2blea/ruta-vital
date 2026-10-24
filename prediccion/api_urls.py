from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import predict_risk, all_users_risk
from .api_views import (
    PersonViewSet,
    UserViewSet,
    RoleViewSet,
    PermissionViewSet,
    GlucoseReadingViewSet,
    UserHasRoleViewSet,
    IoTDeviceViewSet,
    predict_risk,
    all_users_risk,
    telemetry_ingest,
    telemetry_status,
    telemetry_dashboard,
)
from .auth_views import api_login, api_register, api_logout, api_reset_password

router = DefaultRouter()
router.register(r'persons',     PersonViewSet,         basename='api-persons')
router.register(r'users',       UserViewSet,           basename='api-users')
router.register(r'roles',       RoleViewSet,           basename='api-roles')
router.register(r'permissions', PermissionViewSet,     basename='api-permissions')
router.register(r'readings',    GlucoseReadingViewSet, basename='api-readings')
router.register(r'user-roles', UserHasRoleViewSet,    basename='api-user-roles')
router.register(r'iot-devices', IoTDeviceViewSet,      basename='api-iot-devices')

urlpatterns = [
    # ── Auth endpoints ────────────────────────────────────────
    path('auth/login/',    api_login,    name='api-login'),
    path('auth/register/', api_register, name='api-register'),
    path('auth/logout/',   api_logout,   name='api-logout'),
    path('auth/reset-password/', api_reset_password, name='api-reset-password'),

    path('predictions/risk/',       predict_risk,      name='predict-risk'),
    path('predictions/all-risks/',  all_users_risk,    name='all-risks'),

    path('telemetry/ingest/',     telemetry_ingest,     name='telemetry-ingest'),
    path('telemetry/status/',     telemetry_status,     name='telemetry-status'),
    path('telemetry/dashboard/',  telemetry_dashboard,  name='telemetry-dashboard'),

    # ── REST ViewSets ─────────────────────────────────────────
    path('', include(router.urls)),
]