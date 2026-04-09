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
# LÓGICA DE RECOMENDACIONES AVANZADA
# Based on ADA (American Diabetes Association) clinical guidelines
# ─────────────────────────────────────────────

def build_recommendation(reading: GlucoseReading) -> dict:
    """
    Generates a context-aware recommendation based on:
    - The classified status (hypoglycemia / normal / prediabetes / high_glucose)
    - The measurement context (fasting / postprandial / random)
    - The actual glucose value for more precise advice
    """
    status  = reading.status
    context = reading.context
    value   = reading.glucose_value

    # ── HYPOGLYCEMIA ──────────────────────────────────────────
    # Threshold is universal regardless of context (< 70 mg/dL)
    if status == 'hypoglycemia':
        if value < 54:
            # Severe hypoglycemia — immediate action required
            return {
                'immediate_action':  'Tu nivel es críticamente bajo. Consume de inmediato azúcar de absorción rápida: 3-4 tabletas de glucosa, media taza de jugo de fruta o refresco regular (no diet), o 1 cucharada de miel.',
                'additional_advice': 'Busca atención médica de urgencia si no mejoras en 15 minutos o si pierdes la consciencia. No conduzcas ni operes maquinaria.',
                'when_to_measure':   'Vuelve a medir en 15 minutos. Si sigue por debajo de 70 mg/dL, repite la ingesta.',
                'medical_warning':   True,
            }
        else:
            # Mild-moderate hypoglycemia (54–69 mg/dL)
            return {
                'immediate_action':  'Consume 15g de azúcar de absorción rápida: un vaso de jugo natural, 3 caramelos regulares o un vaso de agua con 1 cucharada de azúcar.',
                'additional_advice': 'Después de 15 minutos vuelve a medir. Si ya superaste 70 mg/dL, consume un snack con carbohidratos y proteína para estabilizar (ej: galletas con queso).',
                'when_to_measure':   'En 15 minutos. Luego en 1 hora para confirmar estabilidad.',
                'medical_warning':   True,
            }

    # ── NORMAL ────────────────────────────────────────────────
    elif status == 'normal':
        if context == 'fasting':
            return {
                'immediate_action':  '¡Excelente! Tu glucosa en ayunas está en rango óptimo. Puedes desayunar normalmente priorizando proteínas y grasas saludables antes que carbohidratos simples.',
                'additional_advice': 'Mantén este resultado evitando snacks azucarados antes de dormir y haciendo al menos 30 minutos de actividad física al día.',
                'when_to_measure':   'Continúa con tu rutina habitual. Próxima medición en ayunas en 1-2 días.',
                'medical_warning':   False,
            }
        elif context == 'postprandial':
            return {
                'immediate_action':  '¡Muy bien! Tu glucosa postprandial es normal. Tu cuerpo está procesando los carbohidratos correctamente.',
                'additional_advice': 'Para mantener este resultado, prefiere comidas con bajo índice glucémico: legumbres, vegetales, proteínas magras y grasas saludables. Evita el sedentarismo después de comer.',
                'when_to_measure':   'Puedes medir en ayunas mañana para tener una visión completa de tu control glucémico.',
                'medical_warning':   False,
            }
        else:
            # Random
            return {
                'immediate_action':  '¡Tu nivel de glucosa está dentro del rango normal! Mantén tus hábitos actuales de alimentación e hidratación.',
                'additional_advice': 'Continúa hidratándote bien (mínimo 8 vasos de agua al día) y mantén una alimentación balanceada.',
                'when_to_measure':   'En tu próxima rutina habitual. Si tienes factores de riesgo, mide en ayunas mañana.',
                'medical_warning':   False,
            }

    # ── PREDIABETES ───────────────────────────────────────────
    elif status == 'prediabetes':
        if context == 'fasting':
            return {
                'immediate_action':  'Tu glucosa en ayunas está elevada (zona de prediabetes). No consumas carbohidratos simples en tu desayuno: evita pan blanco, jugos, azúcar y cereales procesados. Prioriza huevos, aguacate o proteínas.',
                'additional_advice': 'Realiza una caminata de 30 minutos hoy. Reducir 5-7% del peso corporal si tienes sobrepeso puede revertir la prediabetes. Consulta a un médico para seguimiento.',
                'when_to_measure':   'Mide nuevamente en ayunas mañana para confirmar la tendencia. Si persiste, agenda una consulta médica.',
                'medical_warning':   False,
            }
        elif context == 'postprandial':
            return {
                'immediate_action':  'Tu glucosa postprandial está algo elevada. Da una caminata de 20-30 minutos ahora — caminar después de comer es una de las estrategias más efectivas para reducir el pico glucémico.',
                'additional_advice': 'Revisa qué comiste: los carbohidratos refinados (arroz blanco, pan, pastas, dulces) elevan la glucosa rápidamente. En tu próxima comida reduce las porciones de estos alimentos y agrega más vegetales y proteínas.',
                'when_to_measure':   'Mide en 2 horas para ver cómo evoluciona. También mide mañana en ayunas.',
                'medical_warning':   False,
            }
        else:
            # Random
            return {
                'immediate_action':  'Tu lectura está en zona de alerta. Evita consumir alimentos o bebidas con azúcar por las próximas 2 horas y realiza actividad física ligera (caminar 20 minutos).',
                'additional_advice': 'Para un diagnóstico más preciso, lo ideal es medir en ayunas. Esta lectura aleatoria puede verse afectada por lo que comiste recientemente.',
                'when_to_measure':   'Mide mañana en ayunas para una lectura más confiable.',
                'medical_warning':   False,
            }

    # ── HIGH GLUCOSE ──────────────────────────────────────────
    elif status == 'high_glucose':
        if context == 'fasting':
            return {
                'immediate_action':  'Tu glucosa en ayunas está significativamente elevada. Esto requiere atención médica. Bebe un vaso grande de agua ahora y evita cualquier alimento azucarado o carbohidrato simple en el desayuno.',
                'additional_advice': 'Este nivel en ayunas puede indicar diabetes. Es fundamental que consultes a un médico pronto. Si ya tienes medicación prescrita, sigue exactamente las indicaciones de tu médico.',
                'when_to_measure':   'Mide en 2 horas. Si el valor sigue por encima de 200 mg/dL, busca atención médica hoy.',
                'medical_warning':   True,
            }
        elif context == 'postprandial':
            if value < 250:
                return {
                    'immediate_action':  'Tu glucosa postprandial está elevada. Bebe agua (no jugos ni bebidas azucaradas) y da una caminata de 30 minutos para ayudar a tu cuerpo a procesar el azúcar.',
                    'additional_advice': 'Revisa el contenido de tu última comida. Para controlar mejor los picos postprandiales: reduce porciones de carbohidratos, come más despacio, e incluye siempre vegetales y proteínas en cada comida.',
                    'when_to_measure':   'Mide en 2 horas. También mide mañana en ayunas para evaluar tu control general.',
                    'medical_warning':   False,
                }
            else:
                return {
                    'immediate_action':  'Tu glucosa postprandial está muy elevada. Bebe agua abundante, evita cualquier alimento por las próximas 3 horas y realiza actividad física ligera si te sientes bien.',
                    'additional_advice': 'Si tienes medicación para la diabetes, consulta a tu médico sobre el ajuste de dosis. No te automediques con insulina sin indicación médica.',
                    'when_to_measure':   'Mide en 1 hora. Si no baja o tienes síntomas (mareo, visión borrosa, sed extrema), busca atención médica hoy.',
                    'medical_warning':   True,
                }
        else:
            # Random
            return {
                'immediate_action':  'Tu nivel de glucosa está muy elevado. Bebe agua inmediatamente, evita cualquier alimento azucarado y descansa. Si tienes síntomas como sed extrema, visión borrosa o mareo, busca atención médica.',
                'additional_advice': 'Esta lectura aleatoria requiere confirmación. Mide en ayunas mañana para un diagnóstico más preciso. Si ya tienes diagnóstico de diabetes, sigue las indicaciones de tu médico.',
                'when_to_measure':   'En 2 horas. Si persiste elevado, consulta a tu médico.',
                'medical_warning':   True,
            }

    # Fallback
    return {
        'immediate_action':  'Consulta a tu médico para interpretar este resultado.',
        'additional_advice': '',
        'when_to_measure':   'Según indicación médica.',
        'medical_warning':   False,
    }