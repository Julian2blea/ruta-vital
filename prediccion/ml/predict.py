"""
Módulo de inferencia — carga el modelo entrenado y realiza predicciones.
"""
import os
import joblib
import numpy as np

from prediccion.ml.features import (
    extract_user_risk_features,
    extract_features_from_reading,
    RISK_LABELS,
)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'modelo_riesgo.pkl'
)

_pipeline = None  # cache en memoria


def get_pipeline():
    """Carga el pipeline una sola vez (singleton)."""
    global _pipeline
    if _pipeline is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Modelo no encontrado. Ejecuta: python manage.py train_model"
            )
        _pipeline = joblib.load(MODEL_PATH)
    return _pipeline


def predict_user_risk(user):
    """
    Predice el nivel de riesgo glucémico de un usuario basado en
    sus últimas 10 lecturas.

    Retorna un dict con:
      - risk_level:      0, 1 o 2
      - risk_label:      'Riesgo Bajo' / 'Riesgo Medio' / 'Riesgo Alto'
      - risk_percentage: 0-100 (probabilidad de la clase predicha)
      - color:           código hex para la interfaz
      - icon:            nombre del ícono FontAwesome
      - features_used:   cantidad de lecturas analizadas
    """
    features = extract_user_risk_features(user, n_readings=10)

    if features is None:
        return {
            'risk_level':      None,
            'risk_label':      'Sin datos suficientes',
            'risk_percentage': None,
            'color':           '#94A3B8',
            'icon':            'question-circle',
            'features_used':   0,
        }

    pipeline   = get_pipeline()
    X          = features.reshape(1, -1)
    risk_level = int(pipeline.predict(X)[0])
    proba      = pipeline.predict_proba(X)[0]
    risk_pct   = round(float(proba[risk_level]) * 100, 1)

    from prediccion.models import GlucoseReading
    n_readings = GlucoseReading.objects.filter(user=user).count()

    info = RISK_LABELS[risk_level]
    return {
        'risk_level':      risk_level,
        'risk_label':      info['label'],
        'risk_percentage': risk_pct,
        'color':           info['color'],
        'icon':            info['icon'],
        'features_used':   min(n_readings, 10),
    }


def predict_single_reading_risk(reading):
    """
    Predicción rápida basada en UNA sola lectura.
    Útil para la app móvil inmediatamente tras registrar.
    """
    features  = extract_features_from_reading(reading)
    pipeline  = get_pipeline()
    X         = features.reshape(1, -1)

    # El pipeline fue entrenado con 12 features de usuario
    # Para una lectura individual usamos heurística clínica directa
    v = reading.glucose_value
    if v < 70 or v >= 200:
        risk_level = 2
    elif 100 <= v <= 125 or 140 <= v <= 199:
        risk_level = 1
    else:
        risk_level = 0

    info = RISK_LABELS[risk_level]
    return {
        'risk_level':      risk_level,
        'risk_label':      info['label'],
        'color':           info['color'],
        'icon':            info['icon'],
    }