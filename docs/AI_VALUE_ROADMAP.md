# Hoja de Ruta: BetControl AI - Generación de Valor Real

Este documento define las funcionalidades críticas para transformar BetControl de un gestor de apuestas pasivo a un **Asesor Inteligente Activo**, impulsado por IA.

## 1. Módulo "David vs Goliat" (Detección de Desequilibrios)
**Objetivo:** Identificar automáticamente partidos donde un equipo "Top" (parte alta de la tabla/alta forma) enfrenta a un equipo "Débil" (parte baja/mala forma), sugiriendo apuestas de alta probabilidad.

### Funcionalidad Técnica Requerida:
- **Ingesta de Tablas de Posiciones (Standings):** El sistema debe conocer la posición real de cada equipo en su liga (1º vs 18º).
- **Análisis de Forma Reciente:** No solo "ganó/perdió", sino "goles anotados vs recibidos" en los últimos 5 juegos.
- **Motor de Reglas IA:**
    - *Input:* Diferencia de puntos en tabla > X, Diferencia de Elo > Y.
    - *Output:* "Oportunidad Alta: Real Madrid (1º) vs Almería (20º) - Probabilidad Victoria 85%".

### Valor para el Usuario:
- Ahorra tiempo buscando en múltiples ligas.
- Filtra el ruido y muestra solo las "apuestas seguras" (teóricas).

## 2. Asesor de Mercados Específicos (Smart Markets)
**Objetivo:** Que la IA no solo diga "Gana Local", sino que sugiera el mercado más rentable.

### Funcionalidad Técnica:
- **Análisis de Goles (Over/Under):**
    - Si ambos equipos promedian +2.5 goles por partido -> Sugerir "Over 2.5 Goles".
- **Ambos Marcan (BTTS):**
    - Si ambos tienen defensas débiles -> Sugerir "BTTS - Sí".
- **Hándicap Asiático:**
    - Si la diferencia de Elo es masiva -> Sugerir "Local -1.5".

### Valor para el Usuario:
- Diversifica las opciones de apuesta más allá del simple "Ganador del Partido".
- Maximiza la cuota buscando mercados alternativos con alta probabilidad.

## 3. "El Oráculo" (Validador Interactivo de Apuestas)
**Objetivo:** Una interfaz donde el usuario dice "¿Qué opinas de apostar al Arsenal hoy?" y la IA responde con datos.

### Flujo:
1.  Usuario selecciona un partido de la lista del día.
2.  Usuario selecciona una intención (ej. "Creo que gana Arsenal").
3.  **IA Analiza y Responde:**
    -   *Semáforo Verde:* "Buena opción. Arsenal tiene 80% de prob. y el rival tiene 3 bajas."
    -   *Semáforo Rojo:* "Riesgo Alto. Arsenal juega con suplentes y el rival es fuerte en casa."

## 4. Dashboard de Oportunidades del Día (Real-Time Value)
**Objetivo:** Resolver el problema de "No hay predicciones". El sistema debe mostrar siempre las mejores oportunidades de las próximas 24-48 horas.

### Funcionalidad Técnica:
- **Cronjob Optimizado:** Si no hay juegos "Hoy", buscar automáticamente "Mañana" o "Sábado".
- **Filtro de Ligas:** Priorizar Premier League, La Liga, Serie A, Bundesliga (donde hay más datos y fiabilidad).
- **Visualización:** Tarjetas claras con: Partido, Hora, Predicción IA, % Confianza, Cuota Sugerida.

## 5. Gestión de Bankroll Impulsada por IA (Stake Inteligente)
**Objetivo:** Que la IA sugiera CUÁNTO apostar, no solo A QUIÉN.

### Funcionalidad:
- Basado en el Kelly Criterion ajustado.
- Si la confianza es 90% -> Sugerir Stake Alto (ej. 5%).
- Si la confianza es 55% -> Sugerir Stake Bajo (ej. 1%).

---

## Plan de Ejecución Inmediata
1.  **Arreglar la visualización de predicciones:** Asegurar que `AIService` traiga datos reales de ligas mayores hoy/mañana.
2.  **Implementar "Standings Fetcher":** Conectar con la API para obtener las tablas de posiciones.
3.  **Entrenar Modelo Específico (Goles):** Crear un sub-modelo para predecir Over/Under 2.5.
