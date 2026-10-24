"""
Entrenamiento del clasificador de riesgo glucémico.
Combina datos reales de la DB con datos sintéticos clínicamente válidos
para garantizar que el modelo funcione incluso con pocos datos reales.
"""
import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ml', 'modelo_riesgo.pkl'
)


def generate_synthetic_data(n_samples=1200):
    """
    Genera datos sintéticos basados en rangos ADA 2024.
    Garantiza que el modelo tenga suficientes ejemplos de cada clase.
    """
    np.random.seed(42)
    X, y = [], []

    samples_per_class = n_samples // 3

    # ── Clase 0: Riesgo Bajo (lecturas normales) ─────────────────────────────
    for _ in range(samples_per_class):
        avg   = np.random.uniform(75, 99)
        mx    = avg + np.random.uniform(0, 20)
        mn    = avg - np.random.uniform(0, 15)
        std   = np.random.uniform(5, 18)
        X.append([avg, mx, mn, std,
                  0.0, 0.0, 0.95,
                  np.random.randint(3, 15),
                  np.random.randint(0, 3),
                  np.random.uniform(6, 22),
                  np.random.randint(1, 10),
                  np.random.uniform(-8, 8)])
        y.append(0)

    # ── Clase 1: Riesgo Medio (prediabetes / irregularidad) ──────────────────
    for _ in range(samples_per_class):
        avg   = np.random.uniform(100, 145)
        mx    = avg + np.random.uniform(10, 40)
        mn    = avg - np.random.uniform(5, 25)
        std   = np.random.uniform(15, 35)
        X.append([avg, mx, mn, std,
                  np.random.uniform(0.1, 0.3),
                  np.random.uniform(0.3, 0.6),
                  np.random.uniform(0.2, 0.5),
                  np.random.randint(3, 15),
                  np.random.randint(0, 3),
                  np.random.uniform(6, 22),
                  np.random.randint(1, 10),
                  np.random.uniform(5, 25)])
        y.append(1)

    # ── Clase 2: Riesgo Alto (hiperglucemia / hipoglucemia frecuente) ─────────
    for _ in range(samples_per_class):
        avg   = np.random.uniform(160, 280)
        mx    = avg + np.random.uniform(20, 60)
        mn    = avg - np.random.uniform(10, 50)
        std   = np.random.uniform(30, 70)
        X.append([avg, mx, mn, std,
                  np.random.uniform(0.4, 0.9),
                  np.random.uniform(0.0, 0.3),
                  np.random.uniform(0.0, 0.2),
                  np.random.randint(3, 15),
                  np.random.randint(0, 3),
                  np.random.uniform(6, 22),
                  np.random.randint(1, 10),
                  np.random.uniform(15, 60)])
        y.append(2)

    return np.array(X), np.array(y)


def load_real_data():
    """
    Carga datos reales agrupados por usuario desde la base de datos.
    Requiere contexto de Django activo (llamar desde manage.py).
    """
    from prediccion.models import User
    from prediccion.ml.features import extract_user_risk_features, STATUS_MAP

    X_real, y_real = [], []

    for user in User.objects.filter(is_staff=False).prefetch_related('readings'):
        features = extract_user_risk_features(user, n_readings=10)
        if features is None:
            continue

        readings = user.readings.order_by('-reading_date')[:10]
        statuses = [r.status for r in readings]
        if not statuses:
            continue

        critical_pct    = sum(1 for s in statuses if s in ('high_glucose', 'hypoglycemia')) / len(statuses)
        prediabetes_pct = sum(1 for s in statuses if s == 'prediabetes') / len(statuses)

        if critical_pct >= 0.4:
            label = 2
        elif prediabetes_pct >= 0.3 or critical_pct >= 0.1:
            label = 1
        else:
            label = 0

        X_real.append(features)
        y_real.append(label)

    return np.array(X_real) if X_real else None, np.array(y_real) if y_real else None


def train_and_save():
    """
    Entrena el modelo combinando datos sintéticos y reales.
    Guarda el pipeline (scaler + clasificador) en modelo_riesgo.pkl
    """
    print("Generando datos sintéticos de entrenamiento...")
    X_synth, y_synth = generate_synthetic_data(n_samples=1200)

    print("Cargando datos reales de la base de datos...")
    X_real, y_real = load_real_data()

    if X_real is not None and len(X_real) > 0:
        X = np.vstack([X_synth, X_real])
        y = np.concatenate([y_synth, y_real])
        print(f"  Datos reales incorporados: {len(X_real)} usuarios")
    else:
        X, y = X_synth, y_synth
        print("  Sin datos reales suficientes — usando solo datos sintéticos")

    print(f"Total de muestras de entrenamiento: {len(X)}")
    print(f"Distribución de clases: {dict(zip(*np.unique(y, return_counts=True)))}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=4,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        ))
    ])

    print("\nEntrenando RandomForestClassifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\nReporte de evaluación:")
    print(classification_report(
        y_test, y_pred,
        target_names=['Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto']
    ))

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModelo guardado en: {MODEL_PATH}")
    return pipeline