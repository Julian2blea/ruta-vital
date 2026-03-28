from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    PerfilUsuario, Encuesta, DatosSalud, HabitosAlimenticios,
    EstiloVida, Sintomas, ResultadoEvaluacion
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para PerfilUsuario"""
    usuario = UserSerializer(read_only=True)
    
    class Meta:
        model = PerfilUsuario
        fields = ['id', 'usuario', 'fecha_registro']
        read_only_fields = ['id', 'fecha_registro']


class DatosSaludSerializer(serializers.ModelSerializer):
    """Serializer para DatosSalud"""
    
    class Meta:
        model = DatosSalud
        fields = [
            'id', 'encuesta', 'nombre', 'edad', 'sexo', 
            'peso', 'estatura', 'imc', 'antecedentes_familiares'
        ]
        read_only_fields = ['id']


class HabitosAlimenticiosSerializer(serializers.ModelSerializer):
    """Serializer para HabitosAlimenticios"""
    
    class Meta:
        model = HabitosAlimenticios
        fields = [
            'id', 'encuesta', 'frecuencia_ultraprocesados', 
            'consume_frutas_verduras', 'desayuna_regularmente',
            'numero_comidas', 'frecuencia_bebidas_azucaradas',
            'frecuencia_grasa_saturada', 'consumo_integrales'
        ]
        read_only_fields = ['id']


class EstiloVidaSerializer(serializers.ModelSerializer):
    """Serializer para EstiloVida"""
    
    class Meta:
        model = EstiloVida
        fields = ['id', 'encuesta', 'ejercicio_regular', 'estres_cronico', 'duerme_bien']
        read_only_fields = ['id']


class SintomasSerializer(serializers.ModelSerializer):
    """Serializer para Sintomas"""
    
    class Meta:
        model = Sintomas
        fields = [
            'id', 'encuesta', 'cambios_peso', 'fatiga_frecuente',
            'problemas_digestivos', 'examenes_sangre'
        ]
        read_only_fields = ['id']


class ResultadoEvaluacionSerializer(serializers.ModelSerializer):
    """Serializer para ResultadoEvaluacion"""
    
    class Meta:
        model = ResultadoEvaluacion
        fields = [
            'id', 'encuesta', 'enfermedades_detectadas',
            'nivel_riesgo', 'puntaje_riesgo', 'recomendaciones'
        ]
        read_only_fields = ['id']


class EncuestaSerializer(serializers.ModelSerializer):
    """Serializer para Encuesta con relaciones anidadas"""
    usuario = UserSerializer(read_only=True)
    datos_salud = DatosSaludSerializer(many=True, read_only=True)
    habitos = HabitosAlimenticiosSerializer(many=True, read_only=True)
    estilo_vida = EstiloVidaSerializer(many=True, read_only=True)
    sintomas = SintomasSerializer(many=True, read_only=True)
    resultados = ResultadoEvaluacionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Encuesta
        fields = [
            'id', 'usuario', 'fecha_creacion',
            'datos_salud', 'habitos', 'estilo_vida',
            'sintomas', 'resultados'
        ]
        read_only_fields = ['id', 'fecha_creacion']