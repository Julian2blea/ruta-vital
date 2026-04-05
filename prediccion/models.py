from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
 
 
# ─────────────────────────────────────────────────────────────
# PERSON
# ─────────────────────────────────────────────────────────────
 
class Person(models.Model):
    """Informacion personal — separada de los datos de autenticacion"""
 
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
 
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    birth_date  = models.DateField(null=True, blank=True)
    gender      = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone       = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)
 
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
 
    class Meta:
        db_table = 'person'
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'
 
 
# ─────────────────────────────────────────────────────────────
# ROLE & PERMISSION
# ─────────────────────────────────────────────────────────────
 
class Permission(models.Model):
    """Sistema de permisos (e.g. 'can_view_history', 'can_register_reading')"""
 
    description = models.CharField(max_length=200, unique=True)
 
    def __str__(self):
        return self.description
 
    class Meta:
        db_table = 'permission'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
 
 
class Role(models.Model):
    """User role (e.g. 'patient', 'admin', 'doctor')"""
 
    description = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RoleHasPermission',
        related_name='roles',
        blank=True
    )
 
    def __str__(self):
        return self.description
 
    class Meta:
        db_table = 'role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
 
 
class RoleHasPermission(models.Model):
    """a traves de la tabla  role ↔ permission"""
 
    role        = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission  = models.ForeignKey(Permission, on_delete=models.CASCADE)
 
    class Meta:
        db_table = 'role_has_permission'
        unique_together = ('role', 'permission')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
 
 
# ─────────────────────────────────────────────────────────────
# CUSTOM USER
# ─────────────────────────────────────────────────────────────
 
class UserManager(BaseUserManager):
    """Administrador para el modelo de usuario personalizado"""
 
    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError('Login field is required.')
        user = self.model(login=login, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(login, password, **extra_fields)
 
 
class User(AbstractBaseUser, PermissionsMixin):
    """
    Usuario de autenticación personalizada.
    - 'login' reemplaza el nombre de usuario predeterminado de Django.
    - Links a Person para datos personales.
    - Links a Role a traves de UserHasRole.
    """
 
    login       = models.CharField(max_length=150, unique=True)
    person      = models.OneToOneField(
                    Person, on_delete=models.SET_NULL,
                    null=True, blank=True, related_name='user'
                  )
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
 
    roles = models.ManyToManyField(
        Role,
        through='UserHasRole',
        related_name='users',
        blank=True
    )
 
    objects = UserManager()
 
    USERNAME_FIELD  = 'login'
    REQUIRED_FIELDS = []
 
    def __str__(self):
        return self.login
 
    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
 
 
class UserHasRole(models.Model):
    """A traves de la tabla user ↔ role"""
 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
 
    class Meta:
        db_table = 'user_has_role'
        unique_together = ('user', 'role')
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
 
 
# ─────────────────────────────────────────────────────────────
# GLUCOSE MONITORING
# ─────────────────────────────────────────────────────────────
 
class GlucoseReading(models.Model):
    """
    Una única lectura de glucosa en sangre.
    El valor se introduce manualmente o se simula mediante API.
    Unidad: mg/dL.
    """
 
    STATUS_CHOICES = [
        ('hypoglycemia', 'Hypoglycemia'),
        ('normal',       'Normal'),
        ('prediabetes',  'Prediabetes'),
        ('high_glucose', 'High Glucose'),
    ]
 
    CONTEXT_CHOICES = [
        ('fasting',      'Fasting'),
        ('postprandial', 'Postprandial (after meal)'),
        ('random',       'Random'),
    ]
 
    SOURCE_CHOICES = [
        ('manual',    'Manual entry'),
        ('simulated', 'Simulated by app'),
        ('device',    'External device'),
    ]
 
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='readings')
    glucose_value = models.FloatField(help_text="Blood glucose level in mg/dL")
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    context       = models.CharField(max_length=20, choices=CONTEXT_CHOICES, default='random')
    source        = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    notes         = models.TextField(blank=True)
    reading_date  = models.DateTimeField(auto_now_add=True)
 
    def save(self, *args, **kwargs):
        """Auto-classify status before saving"""
        self.status = self._classify()
        super().save(*args, **kwargs)
 
    def _classify(self):
        v = self.glucose_value
        if v < 70:
            return 'hypoglycemia'
        elif v <= 99:
            return 'normal'
        elif v <= 125:
            return 'prediabetes'
        else:
            return 'high_glucose'
 
    def __str__(self):
        return f"{self.user.login} — {self.glucose_value} mg/dL ({self.status})"
 
    class Meta:
        db_table = 'glucose_reading'
        verbose_name = 'Glucose Reading'
        verbose_name_plural = 'Glucose Readings'
        ordering = ['-reading_date']
 
 
class GlucoseRecommendation(models.Model):
    """
    Recomendación generada automáticamente en función de una lectura de glucosa.
    Una lectura → una recomendación (OneToOne).
    """
 
    reading           = models.OneToOneField(GlucoseReading, on_delete=models.CASCADE, related_name='recommendation')
    immediate_action  = models.CharField(max_length=300)
    additional_advice = models.CharField(max_length=300, blank=True)
    when_to_measure   = models.CharField(max_length=100)
    medical_warning   = models.BooleanField(default=False)
    generated_at      = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f"Recommendation for reading {self.reading.id} — {self.reading.status}"
 
    class Meta:
        db_table = 'glucose_recommendation'
        verbose_name = 'Glucose Recommendation'
        verbose_name_plural = 'Glucose Recommendations'
 