from rest_framework import serializers
from .models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission,
    GlucoseReading, GlucoseRecommendation,
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