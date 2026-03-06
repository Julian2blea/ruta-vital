from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    """Información adicional del usuario"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"


class Encuesta(models.Model):
    """Datos completos de la encuesta con predicción incluida"""
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encuestas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    
    nombre = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()
    sexo = models.CharField(max_length=10, choices=[
        ('Hombre', 'Hombre'), 
        ('Mujer', 'Mujer'), 
        ('Otro', 'Otro')
    ])
    peso = models.FloatField(help_text="En kilogramos")
    estatura = models.FloatField(help_text="En centímetros")
    imc = models.FloatField(null=True, blank=True)
    
    antecedentes_familiares = models.TextField(blank=True)
    
    frecuencia_ultraprocesados = models.CharField(max_length=30)
    consume_frutas_verduras = models.BooleanField()
    desayuna_regularmente = models.BooleanField()
    numero_comidas = models.CharField(max_length=20)
    frecuencia_bebidas_azucaradas = models.CharField(max_length=30)
    frecuencia_grasa_saturada = models.CharField(max_length=30)
    consumo_integrales = models.CharField(max_length=30)
    
    ejercicio_regular = models.BooleanField()
    estres_cronico = models.BooleanField()
    duerme_bien = models.BooleanField()
    
    cambios_peso = models.CharField(max_length=20)
    fatiga_frecuente = models.BooleanField()
    problemas_digestivos = models.BooleanField()
    examenes_sangre = models.CharField(max_length=30)
    
    enfermedades_detectadas = models.TextField(blank=True, help_text="Separadas por comas")
    nivel_riesgo = models.CharField(max_length=20, blank=True)
    puntaje_riesgo = models.IntegerField(null=True, blank=True)
    recomendaciones = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"Encuesta de {self.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Encuesta"
        verbose_name_plural = "Encuestas"
        ordering = ['-fecha_creacion']