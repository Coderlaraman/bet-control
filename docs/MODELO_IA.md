# Documentación del Modelo de IA - BetControl (Versión 3.0)

## 1. Visión General
El módulo de Inteligencia Artificial de BetControl tiene como objetivo predecir el resultado de partidos de fútbol (Local, Empate, Visitante) utilizando algoritmos de Machine Learning avanzados. La versión 3.0 introduce mejoras significativas en la calidad de los datos y la ingeniería de características, incorporando ratings Elo, probabilidades implícitas de las casas de apuestas y estadísticas detalladas de juego.

## 2. Fuentes de Datos
Para superar las limitaciones de historial de las APIs gratuitas, hemos implementado una estrategia híbrida de datos:

1.  **Histórico Masivo (2000-2025)**:
    -   **Fuente**: Dataset curado de GitHub (`Club-Football-Match-Data-2000-2025`).
    -   **Contenido**: Más de 9,000 partidos recientes con metadatos ricos (Elo, Odds, Stats).
    -   **Cobertura**: Premier League, La Liga, Serie A, Bundesliga, Ligue 1.
2.  **Datos en Tiempo Real**:
    -   **Fuente**: API-Football.
    -   **Uso**: Sincronización diaria de partidos, resultados y estadísticas recientes para alimentar las predicciones del día.

## 3. Arquitectura del Modelo

### Algoritmo
-   **Modelo**: **XGBoost Classifier** (Extreme Gradient Boosting).
-   **Hiperparámetros V3**:
    -   `n_estimators`: 200
    -   `max_depth`: 6 (Optimizado para evitar sobreajuste).
    -   `learning_rate`: 0.05 (Aprendizaje gradual para mejor generalización).
    -   `objective`: `multi:softprob` (Probabilidades para 3 clases).

### Características de Entrada (Features)
El modelo utiliza 9 variables predictivas clave, seleccionadas por su impacto en la precisión:

1.  **`prob_home` / `prob_away` (Probabilidades de Mercado)**:
    -   **Importancia: ~40%**. El mercado es el predictor más fuerte.
2.  **`elo_diff` (Diferencia de Elo)**:
    -   **Importancia: ~10%**. Captura la jerarquía estructural.
3.  **Forma Reciente (Tiros y Puntos)**:
    -   **Importancia: ~50% (Combinada)**. El volumen de juego (Tiros) y la eficacia (Puntos/Goles) aportan el contexto táctico.

### Variable Objetivo (Target)
-   `0`: Victoria Visitante
-   `1`: Empate
-   `2`: Victoria Local

## 4. Estrategia de Entrenamiento

### Preprocesamiento e Ingeniería de Características
1.  **Cálculo de Rolling Averages**: Se procesan los datos cronológicamente para calcular las estadísticas "previas al partido".
    -   *Prevención de Data Leakage*: Se usa `shift(1)` para asegurar que las estadísticas de un partido no incluyan el resultado de ese mismo partido.
2.  **Imputación de Datos**:
    -   Valores nulos en cuotas se manejan cuidadosamente para no introducir sesgos.
    -   Equipos nuevos o ascendidos inician con valores base (Elo 1500).

### Resultados del Entrenamiento (V3 - XGBoost)
-   **Precisión Global (Accuracy)**: **51%**
    -   *Análisis*: Mantiene la precisión del Random Forest pero con mejor manejo de probabilidades (softprob) y menor riesgo de overfitting gracias a la regularización nativa de XGBoost.
    -   *Desempeño por Clase*:
        -   Victoria Local: 62% F1-Score (Muy sólido).
        -   Empate: 12% F1-Score (El empate sigue siendo difícil de predecir, común en modelos de fútbol).
        -   Victoria Visitante: 53% F1-Score.

## 5. Integración en Producción (AIService)
El servicio de IA (`AIService`) ha sido actualizado para replicar esta lógica en tiempo real:
1.  Consulta el **Elo más reciente** de cada equipo en la base de datos.
2.  Calcula la **probabilidad implícita** (usando Elo si no hay cuotas disponibles).
3.  Agrega las estadísticas de forma (Goles/Puntos) desde la API.
4.  Genera una predicción con un **Score de Confianza**.

## 6. Próximos Pasos y Recomendaciones
-   **Optimización de Hiperparámetros**: Realizar un Grid Search exhaustivo para exprimir un 1-2% extra de precisión.
-   **Nuevas Features**: Integrar "Días de Descanso" (Fatiga) y "Distancia de Viaje" (Factor Visitante).
