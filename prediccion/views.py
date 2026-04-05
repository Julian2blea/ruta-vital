from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from .models import Person, User, GlucoseReading, GlucoseRecommendation
from .forms import RegisterForm
 
 
# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────
 
def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')
 
 
def registro(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                person = Person.objects.create(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data.get('email', ''),
                )
                User.objects.create_user(
                    login=data['login'],
                    password=data['password'],
                    person=person,
                )
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registro.html', {'form': form})
 
 
def login_usuario(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})
 
 
def cerrar_sesion(request):
    logout(request)
    return redirect('login')
 
 
# ─────────────────────────────────────────────
# VISTAS PRINCIPALES
# ─────────────────────────────────────────────
 
@login_required
def home(request):
    readings = GlucoseReading.objects.filter(
        user=request.user
    ).select_related('recommendation').order_by('-reading_date')[:10]
    return render(request, 'home.html', {'readings': readings})
 
 
@login_required
@transaction.atomic
def register_reading(request):
    if request.method == 'POST':
        try:
            value   = float(request.POST.get('glucose_value', 0))
            context = request.POST.get('context', 'random')
            source  = request.POST.get('source', 'manual')
            notes   = request.POST.get('notes', '')
        except ValueError:
            return render(request, 'lectura.html', {'error': 'Valor inválido.'})
 
        if value < 20 or value > 600:
            return render(request, 'lectura.html', {
                'error': 'El valor debe estar entre 20 y 600 mg/dL.'
            })
 
        reading = GlucoseReading.objects.create(
            user=request.user,
            glucose_value=value,
            context=context,
            source=source,
            notes=notes,
        )
        rec_data = build_recommendation(reading)
        GlucoseRecommendation.objects.create(reading=reading, **rec_data)
        return redirect('reading_result', pk=reading.pk)
 
    return render(request, 'lectura.html')
 
 
@login_required
def reading_result(request, pk):
    try:
        reading = GlucoseReading.objects.select_related(
            'recommendation'
        ).get(pk=pk, user=request.user)
    except GlucoseReading.DoesNotExist:
        return redirect('home')
    return render(request, 'resultado.html', {'reading': reading})
 
 
@login_required
def history(request):
    readings = GlucoseReading.objects.filter(
        user=request.user
    ).order_by('-reading_date')
    return render(request, 'historial.html', {'readings': readings})
 
 
# ─────────────────────────────────────────────
# LÓGICA DE RECOMENDACIONES
# ─────────────────────────────────────────────
 
def build_recommendation(reading: GlucoseReading) -> dict:
    recommendations = {
        'hypoglycemia': {
            'immediate_action':  'Consume de inmediato 15g de azúcar: un vaso de agua con azúcar, jugo natural o 3 caramelos.',
            'additional_advice': 'Vuelve a medir en 15 minutos. Si sigue bajo, repite y busca atención médica.',
            'when_to_measure':   'En 15 minutos.',
            'medical_warning':   True,
        },
        'normal': {
            'immediate_action':  '¡Tu nivel de glucosa está en rango normal! Mantén tus hábitos actuales.',
            'additional_advice': 'Continúa hidratándote bien con agua a lo largo del día.',
            'when_to_measure':   'En tu próxima rutina habitual o en 24 horas.',
            'medical_warning':   False,
        },
        'prediabetes': {
            'immediate_action':  'Da una caminata de 20 a 30 minutos para ayudar a que tus músculos absorban el exceso de glucosa.',
            'additional_advice': 'Evita carbohidratos refinados (pan blanco, arroz, azúcar) en las próximas 2 horas.',
            'when_to_measure':   'En 2 horas, preferiblemente postprandial.',
            'medical_warning':   False,
        },
        'high_glucose': {
            'immediate_action':  'Toma un vaso grande de agua natural y evita alimentos o bebidas con azúcar.',
            'additional_advice': 'Si tienes medicación prescrita, sigue las indicaciones de tu médico.',
            'when_to_measure':   'En 1 hora. Si no baja, consulta a tu médico.',
            'medical_warning':   True,
        },
    }
    return recommendations.get(reading.status, recommendations['normal'])