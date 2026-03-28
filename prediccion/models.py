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
    """Entidad principal de la encuesta"""

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encuestas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Encuesta {self.id} - {self.usuario.username}"

    class Meta:
        verbose_name = "Encuesta"
        verbose_name_plural = "Encuestas"
        ordering = ['-fecha_creacion']


class DatosSalud(models.Model):
    """Datos personales y de salud del usuario"""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='datos_salud')

    nombre = models.CharField(max_length=100)
    edad = models.PositiveIntegerField()

    sexo = models.CharField(
        max_length=10,
        choices=[
            ('Hombre', 'Hombre'),
            ('Mujer', 'Mujer'),
            ('Otro', 'Otro')
        ]
    )

    peso = models.FloatField(help_text="En kilogramos")
    estatura = models.FloatField(help_text="En centímetros")
    imc = models.FloatField(null=True, blank=True)

    antecedentes_familiares = models.TextField(blank=True)

    def __str__(self):
        return f"Datos de salud de {self.nombre}"

    class Meta:
        verbose_name = "Datos de Salud"
        verbose_name_plural = "Datos de Salud"


class HabitosAlimenticios(models.Model):
    """Información sobre hábitos alimenticios"""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='habitos')

    frecuencia_ultraprocesados = models.CharField(max_length=30)
    consume_frutas_verduras = models.BooleanField()
    desayuna_regularmente = models.BooleanField()
    numero_comidas = models.CharField(max_length=20)

    frecuencia_bebidas_azucaradas = models.CharField(max_length=30)
    frecuencia_grasa_saturada = models.CharField(max_length=30)
    consumo_integrales = models.CharField(max_length=30)

    def __str__(self):
        return f"Hábitos alimenticios - Encuesta {self.encuesta.id}"

    class Meta:
        verbose_name = "Hábitos Alimenticios"
        verbose_name_plural = "Hábitos Alimenticios"


class EstiloVida(models.Model):
    """Datos relacionados con estilo de vida"""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='estilo_vida')

    ejercicio_regular = models.BooleanField()
    estres_cronico = models.BooleanField()
    duerme_bien = models.BooleanField()

    def __str__(self):
        return f"Estilo de vida - Encuesta {self.encuesta.id}"

    class Meta:
        verbose_name = "Estilo de Vida"
        verbose_name_plural = "Estilos de Vida"


class Sintomas(models.Model):
    """Síntomas reportados por el usuario"""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='sintomas')

    cambios_peso = models.CharField(max_length=20)
    fatiga_frecuente = models.BooleanField()
    problemas_digestivos = models.BooleanField()
    examenes_sangre = models.CharField(max_length=30)

    def __str__(self):
        return f"Síntomas - Encuesta {self.encuesta.id}"

    class Meta:
        verbose_name = "Síntomas"
        verbose_name_plural = "Síntomas"


class ResultadoEvaluacion(models.Model):
    """Resultado de la predicción de enfermedades"""

    encuesta = models.ForeignKey(Encuesta, on_delete=models.CASCADE, related_name='resultados')

    enfermedades_detectadas = models.TextField(blank=True, help_text="Separadas por comas")
    nivel_riesgo = models.CharField(max_length=20, blank=True)
    puntaje_riesgo = models.IntegerField(null=True, blank=True)

    recomendaciones = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Resultado evaluación - Encuesta {self.encuesta.id}"

    class Meta:
        verbose_name = "Resultado de Evaluación"
        verbose_name_plural = "Resultados de Evaluaciones"