# Documentación del Modelo de IA - BetControl

## 1. Visión General
El objetivo de este módulo es predecir el resultado de partidos de fútbol (Ganador Local, Empate, Ganador Visitante) utilizando técnicas de Machine Learning (Aprendizaje Supervisado).

El modelo se entrena con datos históricos de la temporada 2023 (debido a restricciones de API) y se utilizará para inferencias en la temporada actual, apoyado por un sistema de actualización diaria de datos.

## 2. Arquitectura del Modelo

### Algoritmo Seleccionado
**Random Forest Classifier** (Bosque Aleatorio)
- **Por qué**: Es robusto frente a overfitting, maneja bien variables no lineales y no requiere escalado excesivo de datos. Además, ofrece métricas de "importancia de características" que nos ayudan a explicar el "por qué" de una predicción.

### Variables de Entrada (Features)
El modelo no recibe nombres de equipos, sino métricas de rendimiento derivadas:

1.  **Forma Reciente (Local/Visitante)**:
    -   Puntos obtenidos en los últimos 5 partidos.
    -   Promedio de goles anotados/recibidos en los últimos 5 partidos.
2.  **Factor Localía**:
    -   Rendimiento histórico del equipo jugando en casa vs fuera.
3.  **Enfrentamientos Directos (H2H)**:
    -   (Opcional en V1) Historial de victorias entre ambos equipos.

### Variable Objetivo (Target)
Clasificación Multiclase:
-   `0`: Gana Visitante (Away Win)
-   `1`: Empate (Draw)
-   `2`: Gana Local (Home Win)

## 3. Estrategia de Entrenamiento

### Datos de Entrenamiento
-   **Fuente**: API-Football (vía Backfill script).
-   **Periodo**: Temporada 2023 (Ligas Top 5 de Europa).
-   **Volumen**: ~300-1000 partidos (dependiendo del éxito del backfill).

### Preprocesamiento
1.  **Limpieza**: Eliminar partidos cancelados o sin marcador.
2.  **Feature Engineering**: Calcular medias móviles (Rolling Averages) para simular la "forma" que tenía el equipo *antes* de cada partido. **Crucial**: No usar datos del futuro para predecir el pasado (Data Leakage).

### Validación
-   **Train/Test Split**: 80% para entrenamiento, 20% para validación.
-   **Métrica Principal**: Accuracy (Precisión Global) y F1-Score (para balancear clases, ya que los empates son menos frecuentes).

## 4. Flujo de Inferencia (Predicción Diaria)
1.  El sistema `daily_sync.py` descarga los partidos de hoy.
2.  Calcula las mismas *features* (forma reciente) para los equipos que juegan hoy, basándose en los datos acumulados en la BD.
3.  El modelo `.pkl` predice la probabilidad de cada resultado.
4.  Si la confianza > umbral (ej. 60%), se guarda como sugerencia.

## 5. Reentrenamiento
Se recomienda reentrenar el modelo semanalmente (`scripts/train_model.py`) para que incorpore los nuevos resultados de 2025 a medida que ocurren.
