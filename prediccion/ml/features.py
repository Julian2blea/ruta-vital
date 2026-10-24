"""
Extracción de características para el modelo de riesgo glucémico.
Convierte lecturas brutas en vectores numéricos para scikit-learn.
"""
import numpy as np
from datetime import timedelta
from django.utils import timezone


CONTEXT_MAP = {'fasting': 0, 'postprandial': 1, 'random': 2}
SOURCE_MAP  = {'manual': 0, 'simulated': 1, 'device': 2}
STATUS_MAP  = {'normal': 0, 'prediabetes': 1, 'high_glucose': 2, 'hypoglycemia': 2}

RISK_LABELS = {
    0: {'label': 'Riesgo Bajo',   'color': '#34D399', 'icon': 'check-circle'},
    1: {'label': 'Riesgo Medio',  'color': '#FBBF24', 'icon': 'exclamation-triangle'},
    2: {'label': 'Riesgo Alto',   'color': '#F87171', 'icon': 'times-circle'},
}


def extract_features_from_reading(reading):
    """
    Extrae características de UNA lectura individual.
    Retorna un array numpy de 6 features.
    """
    return np.array([
        reading.glucose_value,
        CONTEXT_MAP.get(reading.context, 2),
        SOURCE_MAP.get(reading.source, 0),
        reading.reading_date.hour,
        reading.reading_date.weekday(),
        1 if reading.glucose_value < 70 or reading.glucose_value > 180 else 0,
    ])


def extract_user_risk_features(user, n_readings=10):
    """
    Extrae características agregadas de las últimas N lecturas de un usuario.
    Retorna un array numpy de 12 features o None si no hay lecturas.

    Features:
      0  avg_glucose        — promedio de glucosa
      1  max_glucose        — valor máximo registrado
      2  min_glucose        — valor mínimo registrado
      3  std_glucose        — desviación estándar
      4  pct_critical       — % lecturas críticas (alta o hipo)
      5  pct_prediabetes    — % lecturas en prediabetes
      6  pct_normal         — % lecturas normales
      7  count_readings     — cantidad de lecturas analizadas
      8  predominant_ctx    — contexto predominante (0=ayunas,1=postprandial,2=aleatorio)
      9  avg_hour           — hora promedio de medición
      10 days_active        — días activos con al menos una lectura
      11 trend              — tendencia: diferencia promedio entre primera y última mitad
    """
    from prediccion.models import GlucoseReading
    from django.db.models import Avg, Max, Min, StdDev

    readings = (
        GlucoseReading.objects
        .filter(user=user)
        .order_by('-reading_date')[:n_readings]
    )

    if not readings:
        return None

    values   = [r.glucose_value for r in readings]
    statuses = [r.status for r in readings]
    contexts = [CONTEXT_MAP.get(r.context, 2) for r in readings]
    hours    = [r.reading_date.hour for r in readings]
    dates    = [r.reading_date.date() for r in readings]
    n        = len(values)

    avg_glucose     = np.mean(values)
    max_glucose     = np.max(values)
    min_glucose     = np.min(values)
    std_glucose     = np.std(values) if n > 1 else 0.0
    pct_critical    = sum(1 for s in statuses if s in ('high_glucose', 'hypoglycemia')) / n
    pct_prediabetes = sum(1 for s in statuses if s == 'prediabetes') / n
    pct_normal      = sum(1 for s in statuses if s == 'normal') / n
    count_readings  = n
    predominant_ctx = max(set(contexts), key=contexts.count) if contexts else 2
    avg_hour        = np.mean(hours)
    days_active     = len(set(dates))

    # Tendencia: promedio primera mitad vs segunda mitad (cronológicamente)
    mid = n // 2
    if mid > 0:
        first_half  = values[mid:]   # más antiguas (orden desc)
        second_half = values[:mid]   # más recientes
        trend = np.mean(second_half) - np.mean(first_half)
    else:
        trend = 0.0

    return np.array([
        avg_glucose, max_glucose, min_glucose, std_glucose,
        pct_critical, pct_prediabetes, pct_normal, count_readings,
        predominant_ctx, avg_hour, days_active, trend
    ])