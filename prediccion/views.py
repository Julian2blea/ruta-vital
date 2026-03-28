from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CuestionarioForm
from django.db import transaction
from .models import (
    Encuesta, PerfilUsuario, DatosSalud, HabitosAlimenticios,
    EstiloVida, Sintomas, ResultadoEvaluacion
)


def landing(request):
    """Página de inicio / Landing page"""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'landing.html')


@login_required
@transaction.atomic
def procesar_cuestionario(request):
    """Procesar el cuestionario y generar predicción"""
    if request.method == 'POST':
        form = CuestionarioForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            peso = float(data.get('peso', 1))
            estatura = float(data.get('estatura', 1))
            imc = calcular_imc(peso, estatura)
            antecedentes = ','.join(data.get('antecedentes_familiares', []))

            enfermedades = predecir_enfermedades(data, imc, antecedentes)
            puntaje = calcular_puntaje_riesgo(data)

            if puntaje <= 4:
                nivel_riesgo = 'Riesgo Bajo'
            elif puntaje <= 8:
                nivel_riesgo = 'Riesgo Moderado'
            else:
                nivel_riesgo = 'Riesgo Alto'

            recomendaciones_generadas = generar_recomendaciones(
                data, imc, antecedentes, enfermedades
            )

            # =============================
            # CREAR TODO EN UNA TRANSACCIÓN
            # =============================
            
            # 1. Crear Encuesta primero
            encuesta = Encuesta(usuario=request.user)
            encuesta.save()

            # 2. Crear Datos de Salud
            datos_salud = DatosSalud(
                encuesta=encuesta,
                nombre=data['nombre'],
                edad=data['edad'],
                sexo={'H': 'Hombre', 'M': 'Mujer', 'O': 'Otro'}[data['sexo']],
                peso=peso,
                estatura=estatura,
                imc=imc,
                antecedentes_familiares=antecedentes
            )
            datos_salud.save()

            # 3. Crear Hábitos Alimenticios
            habitos = HabitosAlimenticios(
                encuesta=encuesta,
                frecuencia_ultraprocesados=data['consumo_ultraprocesados'],
                consume_frutas_verduras=(data['consumo_frutas_verduras'] == 'S'),
                desayuna_regularmente=(data['desayuno_regular'] == 'S'),
                numero_comidas=data['comidas_principales'],
                frecuencia_bebidas_azucaradas=data['bebidas_azucaradas'],
                frecuencia_grasa_saturada=data['consumo_grasas_saturadas'],
                consumo_integrales=data['consumo_integrales']
            )
            habitos.save()

            # 4. Crear Estilo de Vida
            estilo = EstiloVida(
                encuesta=encuesta,
                ejercicio_regular=(data['ejercicio_regular'] == 'S'),
                estres_cronico=(data['estres_cronico'] == 'S'),
                duerme_bien=(data['dormir_7_horas'] == 'S')
            )
            estilo.save()

            # 5. Crear Síntomas
            sintomas = Sintomas(
                encuesta=encuesta,
                cambios_peso=data['cambios_peso'],
                fatiga_frecuente=(data['sensacion_debilidad'] == 'S'),
                problemas_digestivos=(data['dolor_estomacal'] == 'S'),
                examenes_sangre=data['examenes_sangre']
            )
            sintomas.save()

            # 6. Crear Resultado
            resultado = ResultadoEvaluacion(
                encuesta=encuesta,
                enfermedades_detectadas=','.join(enfermedades) if enfermedades else '',
                nivel_riesgo=nivel_riesgo,
                puntaje_riesgo=puntaje,
                recomendaciones=recomendaciones_generadas
            )
            resultado.save()

            return render(request, 'resultado.html', {
                'enfermedades': enfermedades,
                'resultado': nivel_riesgo,
                'recomendaciones': recomendaciones_generadas,
                'nombre': data['nombre']
            })

    else:
        form = CuestionarioForm()

    return render(request, 'cuestionario.html', {'form': form})


def calcular_imc(peso, estatura):
    if estatura == 0:
        return None
    estatura_metros = estatura / 100
    return round(peso / (estatura_metros ** 2), 1)


def calcular_puntaje_riesgo(data):
    puntaje = sum([
        2 if data['consumo_ultraprocesados'] in ['3-5', 'A'] else 0,
        2 if data['bebidas_azucaradas'] in ['V', 'A'] else 0,
        2 if data['ejercicio_regular'] == 'N' else 0,
        1 if data['estres_cronico'] == 'S' else 0,
        1 if data['dormir_7_horas'] == 'N' else 0,
        2 if data['consumo_frutas_verduras'] == 'N' else 0,
        1 if data['consumo_grasas_saturadas'] in ['V', 'A'] else 0
    ])
    return puntaje


def generar_recomendaciones(data, imc, antecedentes, enfermedades):
    recomendaciones = []

    if data['consumo_ultraprocesados'] in ['3-5', 'A']:
        recomendaciones.append({
            'categoria': 'alimentacion',
            'texto': 'Prioriza alimentos frescos y naturales en tu dieta, también ten en cuenta frutas y verduras.',
            'prioridad': 1
        })

    if data['bebidas_azucaradas'] in ['V', 'A']:
        recomendaciones.append({
            'categoria': 'alimentacion',
            'texto': 'Reduce el consumo de bebidas azucaradas, prioriza consumir agua o infusiones.',
            'prioridad': 1
        })

    if imc >= 25 and data['ejercicio_regular'] == 'N':
        recomendaciones.append({
            'categoria': 'ejercicio',
            'texto': 'Realiza actividad física al menos 30 minutos al día como mínimo 3 días a la semana.',
            'prioridad': 1
        })
    elif imc < 25 and data['ejercicio_regular'] == 'S':
        recomendaciones.append({
            'categoria': 'ejercicio',
            'texto': 'Continúa con tu rutina de ejercicio para mantener tu peso saludable.',
            'prioridad': 3
        })

    if data['estres_cronico'] == 'S':
        recomendaciones.append({
            'categoria': 'estilo_vida',
            'texto': 'Practica técnicas de relajación como meditación o respiración profunda.',
            'prioridad': 2
        })

    if data['dormir_7_horas'] == 'N':
        recomendaciones.append({
            'categoria': 'estilo_vida',
            'texto': 'Establece una rutina de sueño y evita pantallas antes de dormir.',
            'prioridad': 2
        })

    antecedentes_lista = antecedentes.split(',') if antecedentes else []

    if 'diabetes' in antecedentes_lista:
        recomendaciones.append({
            'categoria': 'salud',
            'texto': 'Controla tu consumo de carbohidratos refinados y monitorea tus niveles de azúcar.',
            'prioridad': 1
        })

    if 'hipertension' in antecedentes_lista:
        recomendaciones.append({
            'categoria': 'salud',
            'texto': 'Reduce el consumo de sodio y mantén chequeos médicos regulares.',
            'prioridad': 1
        })

    if 'colesterol' in antecedentes_lista:
        recomendaciones.append({
            'categoria': 'alimentacion',
            'texto': 'Prioriza grasas saludables como aguacate, frutos secos y aceite de oliva.',
            'prioridad': 2
        })

    return recomendaciones


def predecir_enfermedades(data, imc, antecedentes):
    enfermedades = set()
    antecedentes_lista = antecedentes.split(',') if antecedentes else []

    if imc >= 30 or ('cardiovascular' in antecedentes_lista):
        enfermedades.add("Obesidad")

    if imc >= 25:
        enfermedades.add("Sobrepeso")

    if 'diabetes' in antecedentes_lista and (imc >= 30 and data['consumo_ultraprocesados'] in ['A', '3-5']):
        enfermedades.add("Diabetes tipo 2")

    if imc >= 30 and data['consumo_ultraprocesados'] in ['A', '3-5'] and data['bebidas_azucaradas'] in ['A', 'V'] and data['ejercicio_regular'] == 'N':
        enfermedades.add("Diabetes tipo 2")

    if 'hipertension' in antecedentes_lista and (data['estres_cronico'] == 'S'):
        enfermedades.add("Hipertensión")

    if data['dormir_7_horas'] == 'N' and data['ejercicio_regular'] == 'N' and data['estres_cronico'] == 'S':
        enfermedades.add("Hipertensión")

    if data['estres_cronico'] == 'S' and data['cambios_peso'] == 'S' and data['dormir_7_horas'] == 'N':
        enfermedades.add("Hipertensión")

    if 'colesterol' in antecedentes_lista and (data['consumo_grasas_saturadas'] in ['A', 'V'] and data['ejercicio_regular'] == 'N'):
        enfermedades.add("Hipercolesterolemia")

    if data['consumo_grasas_saturadas'] in ['A', 'V'] and 'colesterol' in antecedentes_lista and imc >= 25:
        enfermedades.add("Hipercolesterolemia")

    if data['cambios_peso'] == 'S' and data['sensacion_debilidad'] == 'S' and data['examenes_sangre'] in ['A', 'N'] and data['desayuno_regular'] == 'N' and data['comidas_principales'] in ['1', '2']:
        enfermedades.add("Anemia")

    if data['dolor_estomacal'] == 'S' and data['consumo_integrales'] in ['N', 'C'] and data['consumo_ultraprocesados'] in ['A', '3-5']:
        enfermedades.add("Trastornos digestivos")

    return list(enfermedades)


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                PerfilUsuario.objects.create(usuario=user)
            except:
                pass
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})


def login_usuario(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def home(request):
    encuestas = Encuesta.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:5]
    return render(request, 'home.html', {'encuestas': encuestas})


def cerrar_sesion(request):
    logout(request)
    return redirect('login')