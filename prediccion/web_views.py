from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from functools import wraps
import json

from .models import User, GlucoseReading, Role, Permission, RoleHasPermission


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
    users = (
        User.objects
        .select_related('person')
        .prefetch_related('roles')
        .order_by('-date_joined')
    )
    roles = Role.objects.all()
    ctx = {
        'users': users,
        'roles': roles,
        'total': users.count(),
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