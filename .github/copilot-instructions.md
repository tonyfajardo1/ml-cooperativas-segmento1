## Proyecto Final — Análisis y Clustering de Cooperativas del Segmento 1 en Ecuador

**Curso:** Machine Learning

---

### Descripción general

El objetivo de este proyecto es aplicar técnicas de *machine learning* tanto **no supervisado** (clustering) como **semisupervisado** para analizar y clasificar las cooperativas de ahorro y crédito del Segmento 1 en Ecuador según sus características financieras.

Cada cooperativa cuenta con una **calificación de riesgo (rating)** otorgada por agencias externas (A, B, C, etc.). En la **primera parte**, se aplicarán algoritmos de clustering para identificar grupos naturales de cooperativas con perfiles financieros similares, evaluando qué tan coherentes son estos clusters con respecto a los ratings reales. En la **segunda parte**, se entrenarán modelos de aprendizaje semisupervisado que aprovechen tanto datos etiquetados como no etiquetados para predecir los ratings, explorando cómo la información estructural del conjunto completo puede mejorar el desempeño en escenarios de etiquetado limitado.

Este proyecto integra conceptos de análisis exploratorio, selección y normalización de variables financieras, algoritmos de clustering, y métodos de aprendizaje semisupervisado, proporcionando una visión integral del análisis de datos financieros mediante machine learning.

---

### Objetivos específicos

1. **Construir un dataset consolidado** con los principales indicadores financieros de todas las cooperativas del Segmento 1, usando el corte más reciente disponible, mediante un pipeline automatizado de extracción desde PDFs.
2. **Aplicar técnicas de preprocesamiento y normalización** a los datos (manejo de valores faltantes, escalado, selección de variables) que servirán como base común para ambas partes del proyecto.
3. **Implementar y evaluar modelos de clustering** para identificar grupos naturales de cooperativas con comportamientos financieros similares, y comparar estos clusters con los ratings reales mediante métricas de evaluación no supervisadas.
4. **Desarrollar modelos de aprendizaje semisupervisado** (self-training y label propagation) que aprovechen datos sin etiqueta para mejorar la clasificación de ratings bajo diferentes escenarios de disponibilidad de datos etiquetados (5%, 10%, 20%, 40%).
5. **Evaluar y comparar el desempeño** de los modelos semisupervisados versus un baseline supervisado mediante métricas de clasificación (macro F1, balanced accuracy, AUC), analizando el impacto de los hiperparámetros y la fracción de datos etiquetados.
6. **Analizar e interpretar** los resultados desde una perspectiva financiera y técnica, identificando patrones en los clusters, errores de clasificación por clase de rating, e importancia de variables financieras en las predicciones.

---

### Metodología

# PARTE 1: CLUSTERING

1. **Obtención y limpieza de datos:** 
    - Recopilar indicadores financieros del último corte disponible de forma **automática**, a partir de una lista de enlaces a los archivos PDF de los indicadores financieros. Se deberá implementar un proceso que descargue los PDFs y utilice una **LLM mediante API** para transformar la información en una tabla estructurada, lista para ser procesada y analizada en el proyecto.
        - `Extra (opcional)`
        
        <aside>
        💡
        
        Se dará un puntaje extra si su extacción de la data es 100% automática.
        
        </aside>
        
    - Limpiar y unificar los datos (manejo de valores faltantes, escalado, etc.).
2. **Análisis exploratorio (EDA):**
    - Examinar la distribución de los indicadores.
    - Detectar correlaciones y redundancias.
    - Utilizar TSNE para facilitar visualización.
3. **Modelado:**
    - Aplicar al menos tres algoritmos de ***clustering***, de los cuales **uno deberá ser K-Means** como modelo base (*baseline*).
    - Justificar la elección del número de clusters.
4. **Evaluación y validación:**
    - Evaluar la cohesión y separación de los clusters.
    - Comparar con las calificaciones de riesgo utilizando al menos **dos métricas de evaluación** investigadas por el grupo, las cuales deberán ser justificadas y referenciadas adecuadamente en el informe final.
5. **Conclusiones:**
    - Analizar las similitudes y discrepancias entre clusters y ratings.
    - Proponer hipótesis sobre los patrones financieros observados.

# PARTE 2: APRENDIZAJE SEMISUPERVISADO

Usaremos el mismo conjunto de variables financieras. Los labels serán los ratings oficiales de cada cooperativa.

- Objetivo: entrenar modelos que aprovechen datos sin etiqueta para mejorar la clasificación de rating.
- Supuestos: el preprocesamiento y la selección de variables son exactamente los mismos que en la PARTE 1. No se modifica nada de clustering.

### 2.1 Configuración y protocolo

- División de datos:
    - Conjunto total T con N instancias.
    - Fracción etiquetada p ∈ {5%, 10%, 20%, 40%, 60%, 80%}. El resto (1−p) se trata como no etiquetado.
    - Estratificar por rating en el subconjunto etiquetado.
- Hiperparámetro principal del algoritmo semisupervisado:
    - ratio_labeled = p. Reportar desempeño por cada p y su variabilidad.
- Preprocesamiento:
    - Reutilizar escalado, imputación y selección de variables definidos en la PARTE 1.
    - Semilla aleatoria fija para reproducibilidad.
- Validación:
    - 10 repeticiones por cada p con particiones aleatorias estratificadas de la porción etiquetada.

### 2.2 Modelos a implementar

- Baseline supervisado:
    - Random Forest entrenado solo con el conjunto etiquetado.
- Semisupervisados:
    - Self-training: clasificador base = Random Forest. Usar pseudolabels con umbral de confianza τ ∈ {0.6, 0.7, 0.8, 0.9, otros}.
    - Label Propagation/Label Spreading sobre grafo k-NN:
        - k ∈ {5, 10, 20, otros}. Métrica de distancia: euclidiana en el espacio escalado.

### 2.3 Métricas de evaluación

- Macro F1 y Balanced Accuracy por clase y promedio macro.
- Matriz de confusión por p.
- Curva ROC y AUC.
- Ganancia vs baseline:
    - ΔMacro-F1 y ΔBalanced-Acc de cada método semisupervisado respecto al baseline supervisado para cada p.

### 2.4 Análisis y reporte

- Curvas desempeño vs ratio_labeled p para cada método.
- Test estadístico (usar como pivot al baseline supervisado)
- Efecto del umbral de confianza τ y de k en propagación de etiquetas.
- Discusión de errores frecuentes por clase de rating
- Interpretabilidad:
    - Importancia de variables del clasificador base.
    - TSNE de los features que entran al clasificador donde color represente el label.