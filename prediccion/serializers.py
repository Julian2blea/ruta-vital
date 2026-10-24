from rest_framework import serializers
from .models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission,
    GlucoseReading, GlucoseRecommendation,
    IoTDevice, TelemetryLog
)
 
 
# ─────────────────────────────────────────────
# PERSON
# ─────────────────────────────────────────────
 
class PersonSerializer(serializers.ModelSerializer):
 
    class Meta:
        model  = Person
        fields = ['id', 'first_name', 'last_name', 'birth_date', 'gender', 'phone', 'email']
        read_only_fields = ['id']
 
 
# ─────────────────────────────────────────────
# PERMISSION & ROLE
# ─────────────────────────────────────────────
 
class PermissionSerializer(serializers.ModelSerializer):
 
    class Meta:
        model  = Permission
        fields = ['id', 'description']
        read_only_fields = ['id']
 
 
class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
 
    class Meta:
        model  = Role
        fields = ['id', 'description', 'permissions']
        read_only_fields = ['id']
 
 
# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
 
class UserSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)
    roles  = RoleSerializer(many=True, read_only=True)
 
    class Meta:
        model  = User
        fields = ['id', 'login', 'person', 'roles', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
 
 
class UserCreateSerializer(serializers.ModelSerializer):
    """Se utilizara unicamente para el registro; acepta contraseña en texto plano"""
    password = serializers.CharField(write_only=True, min_length=6)
 
    class Meta:
        model  = User
        fields = ['login', 'password']
 
    def create(self, validated_data):
        return User.objects.create_user(
            login=validated_data['login'],
            password=validated_data['password'],
        )
 
 
# ─────────────────────────────────────────────
# GLUCOSE
# ─────────────────────────────────────────────
 
class GlucoseRecommendationSerializer(serializers.ModelSerializer):
 
    class Meta:
        model  = GlucoseRecommendation
        fields = [
            'id',
            'immediate_action',
            'additional_advice',
            'when_to_measure',
            'medical_warning',
            'generated_at',
        ]
        read_only_fields = fields
 
 
class GlucoseReadingSerializer(serializers.ModelSerializer):
    """Lectura — incluye recomendaciones anidadas. Se usa para GET detallados."""
    recommendation = GlucoseRecommendationSerializer(read_only=True)
    user           = UserSerializer(read_only=True)
 
    class Meta:
        model  = GlucoseReading
        fields = [
            'id',
            'user',
            'glucose_value',
            'status',
            'context',
            'source',
            'notes',
            'reading_date',
            'recommendation',
        ]
        read_only_fields = ['id', 'status', 'reading_date', 'user', 'recommendation']
 
 
class GlucoseReadingCreateSerializer(serializers.ModelSerializer):
    """Usado para POST — Solo los campos que envía el usuario."""
 
    class Meta:
        model  = GlucoseReading
        fields = ['glucose_value', 'context', 'source', 'notes']
 
    def validate_glucose_value(self, value):
        if value < 20 or value > 600:
            raise serializers.ValidationError(
                "Glucose value must be between 20 and 600 mg/dL."
            )
        return value
 
 
class GlucoseHistorySerializer(serializers.ModelSerializer):
    """Serializador ligero para list/history — no recomendaciones anidadas."""
 
    class Meta:
        model  = GlucoseReading
        fields = [
            'id',
            'glucose_value',
            'status',
            'context',
            'source',
            'reading_date',
        ]
        read_only_fields = fields


class IoTDeviceSerializer(serializers.ModelSerializer):
    user_login = serializers.CharField(source='user.login', read_only=True)
    readings_count = serializers.SerializerMethodField()

    class Meta:
        model  = IoTDevice
        fields = [
            'id', 'device_id', 'device_name', 'model_info',
            'status', 'last_ping', 'registered_at',
            'user_login', 'readings_count',
        ]

    def get_readings_count(self, obj):
        return obj.telemetry_logs.count()


class TelemetryIngestSerializer(serializers.Serializer):
    """
    Serializer para recibir telemetría desde un dispositivo IoT externo.
    El dispositivo envía device_id + glucose_value + context.
    """
    device_id     = serializers.CharField(max_length=100)
    glucose_value = serializers.FloatField(min_value=20, max_value=600)
    context       = serializers.ChoiceField(
                      choices=['fasting', 'postprandial', 'random'],
                      default='random'
                    )
    notes         = serializers.CharField(max_length=500, required=False, allow_blank=True)
    # Token de autenticación del dispositivo (para no usar JWT de usuario)
    device_token  = serializers.CharField(max_length=200, required=False, allow_blank=True)


class TelemetryLogSerializer(serializers.ModelSerializer):
    device_id   = serializers.CharField(source='device.device_id', read_only=True)
    user_login  = serializers.CharField(source='device.user.login', read_only=True)
    glucose_value = serializers.SerializerMethodField()
    status        = serializers.SerializerMethodField()

    class Meta:
        model  = TelemetryLog
        fields = [
            'id', 'device_id', 'user_login',
            'glucose_value', 'status',
            'received_at', 'signal_ok', 'raw_payload',
        ]

    def get_glucose_value(self, obj):
        return obj.reading.glucose_value if obj.reading else None

    def get_status(self, obj):
        return obj.reading.status if obj.reading else None