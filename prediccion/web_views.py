from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from functools import wraps
import json

from .models import User, GlucoseReading, Role, Permission, RoleHasPermission, IoTDevice, TelemetryLog


# ─── Helpers de acceso ────────────────────────────────────────────────────────

def is_admin_user(user):
    return user.is_authenticated and (
        user.is_staff or
        user.roles.filter(description='admin').exists()
    )

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('web:login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── LOGIN / LOGOUT ───────────────────────────────────────────────────────────

def web_login(request):
    if is_admin_user(request.user):
        return redirect('web:dashboard')

    if request.method == 'POST':
        login_val = request.POST.get('login', '').strip()
        password  = request.POST.get('password', '').strip()
        user = authenticate(request, username=login_val, password=password)

        if user is None:
            messages.error(request, 'Credenciales incorrectas.')
            return render(request, 'web/login.html')

        if not is_admin_user(user):
            messages.error(request, 'Solo administradores pueden acceder al panel web.')
            return render(request, 'web/login.html')

        if not user.is_active:
            messages.error(request, 'Cuenta desactivada.')
            return render(request, 'web/login.html')

        login(request, user)
        return redirect('web:dashboard')

    return render(request, 'web/login.html')


def web_logout(request):
    logout(request)
    return redirect('web:login')


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    total_users    = User.objects.filter(is_staff=False).count()
    total_readings = GlucoseReading.objects.count()
    critical       = GlucoseReading.objects.filter(
        Q(status='high_glucose') | Q(status='hypoglycemia')
    ).count()
    normal_count   = GlucoseReading.objects.filter(status='normal').count()
    normal_pct     = round((normal_count / total_readings * 100) if total_readings > 0 else 0, 1)

    recent_critical = (
        GlucoseReading.objects
        .filter(Q(status='high_glucose') | Q(status='hypoglycemia'))
        .select_related('user', 'user__person')
        .order_by('-reading_date')[:6]
    )

    recent_readings = (
        GlucoseReading.objects
        .select_related('user', 'user__person')
        .order_by('-reading_date')[:8]
    )

    # Mini gráfica últimos 7 días para el dashboard
    seven_days_ago = timezone.now() - timedelta(days=7)
    mini_trend = (
        GlucoseReading.objects
        .filter(reading_date__gte=seven_days_ago)
        .annotate(day=TruncDate('reading_date'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    mini_data = {
        'labels': [str(r['day']) for r in mini_trend],
        'data':   [r['count'] for r in mini_trend],
    }

    ctx = {
        'total_users':     total_users,
        'total_readings':  total_readings,
        'critical':        critical,
        'normal_pct':      normal_pct,
        'recent_critical': recent_critical,
        'recent_readings': recent_readings,
        'mini_data_json':  json.dumps(mini_data),
    }
    return render(request, 'web/dashboard.html', ctx)


# ─── EDA ──────────────────────────────────────────────────────────────────────

@admin_required
def eda(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)

    STATUS_LABELS = {
        'hypoglycemia': 'Hipoglucemia',
        'normal':       'Normal',
        'prediabetes':  'Prediabetes',
        'high_glucose': 'Glucosa Alta',
    }
    STATUS_COLORS = {
        'hypoglycemia': '#F472B6',
        'normal':       '#34D399',
        'prediabetes':  '#FBBF24',
        'high_glucose': '#F87171',
    }

    # 1. Distribución por estado glucémico
    status_qs = GlucoseReading.objects.values('status').annotate(count=Count('id'))
    glucose_dist = {
        'labels': [STATUS_LABELS.get(s['status'], s['status']) for s in status_qs],
        'data':   [s['count'] for s in status_qs],
        'colors': [STATUS_COLORS.get(s['status'], '#94A3B8') for s in status_qs],
    }

    # 2. Lecturas por día (últimos 30 días)
    daily_qs = (
        GlucoseReading.objects
        .filter(reading_date__gte=thirty_days_ago)
        .annotate(day=TruncDate('reading_date'))
        .values('day').annotate(count=Count('id'))
        .order_by('day')
    )
    daily_data = {
        'labels': [str(r['day']) for r in daily_qs],
        'data':   [r['count'] for r in daily_qs],
    }

    # 3. Promedio de glucosa por día (últimos 30 días)
    avg_qs = (
        GlucoseReading.objects
        .filter(reading_date__gte=thirty_days_ago)
        .annotate(day=TruncDate('reading_date'))
        .values('day').annotate(avg=Avg('glucose_value'))
        .order_by('day')
    )
    avg_data = {
        'labels': [str(r['day']) for r in avg_qs],
        'data':   [round(r['avg'], 1) for r in avg_qs],
    }

    # 4. Distribución por contexto de medición
    CONTEXT_LABELS = {
        'fasting':      'En ayunas',
        'postprandial': 'Postprandial',
        'random':       'Aleatorio',
    }
    context_qs = GlucoseReading.objects.values('context').annotate(count=Count('id'))
    context_dist = {
        'labels': [CONTEXT_LABELS.get(c['context'], c['context']) for c in context_qs],
        'data':   [c['count'] for c in context_qs],
        'colors': ['#60A5FA', '#34D399', '#FBBF24'],
    }

    # 5. Distribución por fuente de registro
    SOURCE_LABELS = {
        'manual':    'Manual',
        'simulated': 'Simulada (Digital Twin)',
        'device':    'Dispositivo IoT',
    }
    source_qs = GlucoseReading.objects.values('source').annotate(count=Count('id'))
    source_dist = {
        'labels': [SOURCE_LABELS.get(s['source'], s['source']) for s in source_qs],
        'data':   [s['count'] for s in source_qs],
        'colors': ['#A78BFA', '#F472B6', '#60A5FA'],
    }

    # 6. Top 5 usuarios con más lecturas críticas
    top_critical_qs = (
        GlucoseReading.objects
        .filter(Q(status='high_glucose') | Q(status='hypoglycemia'))
        .values('user__login')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    top_critical = {
        'labels': [t['user__login'] for t in top_critical_qs],
        'data':   [t['count'] for t in top_critical_qs],
    }

    avg_global        = GlucoseReading.objects.aggregate(avg=Avg('glucose_value'))['avg']
    prediabetes_count = GlucoseReading.objects.filter(status='prediabetes').count()
    total             = GlucoseReading.objects.count()

    ctx = {
        'glucose_dist_json':  json.dumps(glucose_dist),
        'daily_data_json':    json.dumps(daily_data),
        'avg_data_json':      json.dumps(avg_data),
        'context_dist_json':  json.dumps(context_dist),
        'source_dist_json':   json.dumps(source_dist),
        'top_critical_json':  json.dumps(top_critical),
        'avg_global':         round(avg_global, 1) if avg_global else 0,
        'prediabetes_count':  prediabetes_count,
        'total_readings':     total,
        'days_analyzed':      30,
    }
    return render(request, 'web/eda.html', ctx)


# ─── USUARIOS ─────────────────────────────────────────────────────────────────

@admin_required
def users_view(request):
    from django.db.models import Q
    import json # Asegúrate de que json esté importado al inicio de web_views.py

    search = request.GET.get('search', '').strip()

    users = (
        User.objects
        .select_related('person')
        .prefetch_related('roles')
        .order_by('-date_joined')
    )

    if search:
        users = users.filter(
            Q(login__icontains=search) |
            Q(person__first_name__icontains=search) |
            Q(person__last_name__icontains=search)
        )
        
    # Construcción del diccionario de roles para el frontend
    user_role_map = {u.id: [r.id for r in u.roles.all()] for u in users}

    roles = Role.objects.all()
    ctx = {
        'users':  users,
        'roles':  roles,
        'total':  users.count(),
        'search': search,
        'user_role_map_json': json.dumps(user_role_map), # Se envía directamente como JSON
    }
    return render(request, 'web/users.html', ctx)


# ─── LECTURAS ─────────────────────────────────────────────────────────────────

@admin_required
def readings_view(request):
    status_filter = request.GET.get('status', '')
    readings = (
        GlucoseReading.objects
        .select_related('user', 'user__person', 'recommendation')
        .order_by('-reading_date')
    )
    if status_filter:
        readings = readings.filter(status=status_filter)

    ctx = {
        'readings':      readings[:60],
        'status_filter': status_filter,
        'total_count':   readings.count(),
        'estados': [
        ('high_glucose', 'Glucosa Alta',  'bs-high'),
        ('prediabetes',  'Prediabetes',   'bs-prediabetes'),
        ('hypoglycemia', 'Hipoglucemia',  'bs-hypo'),
        ('normal',       'Normal',        'bs-normal'),
    ],
    }
    return render(request, 'web/readings.html', ctx)


@admin_required
def risk_panel(request):
    """Vista de panel de riesgo IA para administradores."""
    from prediccion.ml.predict import predict_user_risk

    users   = User.objects.filter(is_staff=False).select_related('person').prefetch_related('readings', 'roles')
    results = []
    model_available = True

    for user in users:
        try:
            risk = predict_user_risk(user)
            readings_count = user.readings.count()
            results.append({
                'user':           user,
                'risk':           risk,
                'readings_count': readings_count,
            })
        except FileNotFoundError:
            model_available = False
            break
        except Exception:
            results.append({
                'user':           user,
                'risk':           {'risk_label': 'Error', 'color': '#94A3B8', 'risk_percentage': None, 'icon': 'question-circle'},
                'readings_count': user.readings.count(),
            })

    results.sort(key=lambda x: (x['risk']['risk_level'] or -1), reverse=True)

    # Estadísticas de riesgo
    total     = len(results)
    high      = sum(1 for r in results if r['risk'].get('risk_level') == 2)
    medium    = sum(1 for r in results if r['risk'].get('risk_level') == 1)
    low       = sum(1 for r in results if r['risk'].get('risk_level') == 0)

    ctx = {
        'results':         results,
        'model_available': model_available,
        'total':           total,
        'high':            high,
        'medium':          medium,
        'low':             low,
    }
    return render(request, 'web/risk_panel.html', ctx)

@admin_required
def digital_twin(request):
    """
    Panel Digital Twin / IoT para administradores.
    Muestra el estado en tiempo real de todos los dispositivos registrados,
    logs de telemetría y el gemelo digital de la red de glucómetros.
    """
    from django.db.models import Count, Avg

    devices = IoTDevice.objects.select_related('user', 'user__person').order_by('-last_ping')
    logs    = TelemetryLog.objects.select_related(
                'device', 'device__user', 'reading'
              ).order_by('-received_at')[:40]

    total_devices  = devices.count()
    active_devices = devices.filter(status='active').count()
    total_logs     = TelemetryLog.objects.count()

    # Lecturas por fuente para el gráfico de origen
    from prediccion.models import GlucoseReading
    from django.db.models import Count as DCount
    source_stats = (
        GlucoseReading.objects
        .values('source')
        .annotate(count=DCount('id'))
        .order_by('-count')
    )

    SOURCE_LABELS = {
        'manual':    'Manual (app móvil)',
        'simulated': 'Digital Twin (simulación)',
        'device':    'IoT (glucómetro físico)',
    }
    source_chart = {
        'labels': [SOURCE_LABELS.get(s['source'], s['source']) for s in source_stats],
        'data':   [s['count'] for s in source_stats],
        'colors': ['#60A5FA', '#F472B6', '#34D399'],
    }

    ctx = {
        'devices':       devices,
        'logs':          logs,
        'total_devices': total_devices,
        'active_devices':active_devices,
        'total_logs':    total_logs,
        'source_chart_json': json.dumps(source_chart),
        'conceptos_40': [
        {'icon': 'satellite-dish', 'color': '#34D399', 'bg': 'rgba(52,211,153,0.12)',
         'title': 'IoT — Internet de las Cosas',
         'desc':  'Endpoint /api/telemetry/ingest/ recibe datos de glucómetros físicos conectados a internet en tiempo real.'},
        {'icon': 'brain', 'color': '#A78BFA', 'bg': 'rgba(167,139,250,0.12)',
         'title': 'IA & Machine Learning',
         'desc':  'RandomForest predice el nivel de riesgo glucémico analizando patrones de las últimas 10 lecturas por paciente.'},
        {'icon': 'cloud', 'color': '#60A5FA', 'bg': 'rgba(96,165,250,0.12)',
         'title': 'Cloud Computing',
         'desc':  'Backend Django en Render, base de datos PostgreSQL administrada. Disponibilidad 24/7 desde cualquier dispositivo.'},
        {'icon': 'clone', 'color': '#F472B6', 'bg': 'rgba(244,114,182,0.12)',
         'title': 'Gemelo Digital (Digital Twin)',
         'desc':  'La simulación de lecturas en la app replica el comportamiento exacto de un glucómetro físico con perfiles clínicos ADA.'},
    ],
    'conceptos_50': [
        {'icon': 'user-md', 'color': '#34D399', 'bg': 'rgba(52,211,153,0.12)',
         'title': 'Human-in-the-Loop',
         'desc':  'La IA predice el riesgo pero el médico/admin decide la intervención. La tecnología amplifica el juicio humano sin reemplazarlo.'},
        {'icon': 'hands-helping', 'color': '#FBBF24', 'bg': 'rgba(251,191,36,0.12)',
         'title': 'Personalización Masiva',
         'desc':  'Cada paciente recibe recomendaciones individualizadas según su valor, contexto y perfil de riesgo único, no respuestas genéricas.'},
        {'icon': 'leaf', 'color': '#A78BFA', 'bg': 'rgba(167,139,250,0.12)',
         'title': 'Sostenibilidad Social',
         'desc':  'Ruta Vital democratiza el acceso a orientación clínica glucémica para comunidades sin acceso regular a especialistas médicos.'},
        {'icon': 'shield-alt', 'color': '#60A5FA', 'bg': 'rgba(96,165,250,0.12)',
         'title': 'Resiliencia del Sistema',
         'desc':  'Arquitectura desacoplada: si el modelo de IA falla, el sistema de clasificación ADA sigue operando de forma independiente.'},
    ],
    }
    return render(request, 'web/digital_twin.html', ctx)

@admin_required
def assign_role_web(request):
    """
    POST /web/users/assign-role/
    Actualiza los roles de un usuario desde el panel web.
    """
    from .models import UserHasRole

    if request.method != 'POST':
        return redirect('web:users')

    user_id  = request.POST.get('user_id')
    role_ids = request.POST.getlist('roles')   

    try:
        target_user = User.objects.get(id=user_id)

       
        if target_user.is_staff and '1' not in role_ids:
            messages.error(request, f'No se puede modificar los roles del superusuario @{target_user.login}.')
            return redirect('web:users')

        # Borrar roles actuales y asignar los seleccionados
        UserHasRole.objects.filter(user=target_user).delete()
        for role_id in role_ids:
            try:
                role = Role.objects.get(id=role_id)
                UserHasRole.objects.get_or_create(user=target_user, role=role)
            except Role.DoesNotExist:
                pass

        messages.success(request, f'Roles de @{target_user.login} actualizados correctamente.')

    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')

    return redirect('web:users')