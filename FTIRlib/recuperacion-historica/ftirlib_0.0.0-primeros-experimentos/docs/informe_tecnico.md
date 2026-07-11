# Informe Técnico: Detector de Grupos Funcionales y Preprocesamiento de Espectros FTIR

**Muestra de Estudio**: Óxido de Grafeno (GO) y Óxido de Grafeno Reducido (rGO)  
**Autor**: Matías Roberto Alemán  
**Fecha**: Junio de 2026  
**Clasificación**: Confidencial / Uso Interno  

---

## Resumen Ejecutivo
Este informe detalla la metodología algorítmica y los resultados experimentales para el procesamiento automático de espectros de infrarrojo por transformada de Fourier (FTIR) de óxidos de grafeno en sus formas oxidada (`GO coque s lav ox.txt`) y reducida (`GO coque s lav red.txt`). Mediante una búsqueda en cuadrícula de 180 combinaciones de suavizado y corrección de línea base, se determinaron los métodos óptimos que maximizan la detección de los grupos funcionales característicos, minimizando la detección de picos espurios debidos al ruido instrumental.

---

## 1. Diseño del Barrido Paramétrico (Grid Search) y Lógica Matemática (Consigna 4.1)

El preprocesamiento de la señal FTIR consta de dos etapas secuenciales fundamentales: el suavizado de ruido de alta frecuencia y la eliminación de la deriva de línea base. Para encontrar la combinación óptima, se diseñó un espacio de búsqueda en cuadrícula (grid search).

### 1.1. Lógica Combinatoria y Fórmula Aritmética
La cantidad total de pruebas independientes ($N_{\text{total}}$) ejecutadas por el pipeline de evaluación se define matemáticamente como el producto del número de configuraciones de suavizado y el número de configuraciones de línea base:

$$N_{\text{total}} = N_{\text{suavizados}} \times N_{\text{baselines}}$$

En nuestra implementación, las configuraciones evaluadas son:

1. **Algoritmos de Suavizado ($N_{\text{suavizados}} = 12$)**:
   - RAW (Sin suavizado) [1]
   - Moving Average (Anchos: 3, 5, 7) [3]
   - Savitzky-Golay (Parámetros: [7,2], [11,2], [15,3]) [3]
   - Median Filter (Anchos: 3, 5, 7) [3]
   - Percentile Filter (Parámetros: [5, 25], [5, 75]) [2]

2. **Algoritmos de Línea Base ($N_{\text{baselines}} = 15$)**:
   - RAW (Sin corrección) [1]
   - Detrend (Eliminación de tendencia lineal) [1]
   - Linear Baseline (Ajuste de extremos) [1]
   - Polynomial Baseline (IModPoly) (Grados: 2, 3, 4) [3]
   - Asymmetric Least Squares (AsLS) ($\lambda \in [10^4, 10^5, 10^6]$, $p=0.001$) [3]
   - airPLS (Mínimos cuadrados penalizados adaptativos) ($\lambda \in [10^4, 10^5, 10^6]$) [3]
   - arPLS (Mínimos cuadrados penalizados asimétricos locales) ($\lambda \in [10^4, 10^5, 10^6]$) [3]

Aplicando la relación combinatoria:

$$N_{\text{total}} = 12 \times 15 = 180 \text{ pruebas}$$

### 1.2. Almacenamiento y Formato en `pipeline_results.csv`
Cada una de las 180 combinaciones se ejecuta de forma secuencial y los resultados de la métrica de detección se registran en el archivo `pipeline_results.csv`. Este archivo contiene las siguientes columnas estructuradas:
- `Smoothing`: Nombre y parámetros del suavizado (ej. `Savitzky_Golay(7, 2)`).
- `Baseline`: Nombre y parámetros de la línea base (ej. `arpls(lam=1e6)`).
- `N_Groups_Detected`: Cantidad de grupos funcionales únicos detectados.
- `Detected_Groups`: Lista separada por comas de las funciones químicas mapeadas.
- `N_Peaks_Detected`: Total de mínimos locales detectados por el algoritmo de picos.
- `N_Noise_Peaks`: Cantidad de picos detectados que no caen en ningún rango del base de datos.
- `Score_Std`: Puntuación estándar: $\text{Total Peaks} + \text{Unique Groups} - \text{Noise Peaks}$.
- `Score_Penalized`: Puntuación penalizada: $\text{Valid Peaks} + \text{Unique Groups} - \text{Noise Peaks}$.

---

## 2. Recreación de "pedido.png" sobre Muestra Reducida (rGO) (Consigna 4.2)

La imagen de referencia `pedido.png` proviene del estudio reológico de nanofluidos de óxido de grafeno (Silva, M.; Rocha Santos Lemos, B.; Viana, M. *Estudo das propriedades reológicas de nanofluidos à base de etilenoglicol e óxido de grafeno*, pág. 6, ResearchGate, 2021). 

Para replicar con precisión de calidad de publicación este gráfico a partir de la muestra de óxido de grafeno reducido (`GO coque s lav red.txt`):
1. **Selección del Preprocesamiento**: Se determinó que la combinación óptima para rGO, penalizando los picos de ruido, es **RAW + arpls(lam=1e6)**.
2. **Formateo Gráfico en Matplotlib**:
   - Se graficó la transmitancia corregida multiplicativamente en color negro con un grosor de línea de $1.0\text{ pt}$.
   - Se invirtió el eje de las abscisas (Número de onda) desde $4000\text{ cm}^{-1}$ hasta $400\text{ cm}^{-1}$.
   - Se ocultaron las etiquetas numéricas del eje Y (Transmitancia), manteniendo las marcas de graduación (ticks) orientadas hacia adentro (`direction='in'`), cumpliendo con la representación de unidades arbitrarias (u.a.).
   - Para cada pico detectado, se trazó una línea roja vertical punteada (`linestyle='--'`) desde el mínimo local hasta la altura de la etiqueta de texto.
   - Las etiquetas de los grupos funcionales (O-H, C-H, CO2, C=O, C=C, C-O, C-O-C) se rotaron a 270 grados (verticales hacia abajo) en color azul.
3. El resultado fue guardado en el archivo de alta resolución **`resultado_best.png`**.

---

## 3. Generación de Vista en Galería A4 para rGO (Consigna 4.3)

Para permitir a los investigadores analizar visualmente los efectos de las mejores combinaciones, se desarrolló el script `plot_gallery_rGO.py`, el cual automatiza la creación de una hoja de prueba en formato A4 horizontal (`resultado_galeria_rGO.png`).

- **Criterio de Inclusión**: Se filtran únicamente aquellas combinaciones en `pipeline_results.csv` que logran la máxima cantidad de grupos funcionales únicos detectados ($N_{\text{Groups\_Detected}} = 7$). Para la muestra rGO, este criterio arrojó **15 configuraciones óptimas**.
- **Distribución en Cuadrícula**: Los subgráficos se disponen en una matriz de $5 \times 3$ (5 filas y 3 columnas), aprovechando perfectamente las dimensiones de una hoja A4.
- **Optimización de Espacio**: Se eliminaron los valores numéricos del eje X en las filas superiores de la cuadrícula para evitar la redundancia y saturación visual. Además, se redujo el tamaño de fuente de las etiquetas de los grupos funcionales a $7\text{ pt}$ y el ancho de las líneas de transmitancia a $0.8\text{ pt}$ para asegurar la legibilidad en tamaño miniatura.

---

## 4. Adaptación y Procesamiento de la Muestra GO (Consigna 4.4)

El procesamiento automático se aplicó a la muestra de Óxido de Grafeno en su estado oxidado sin lavar (`GO coque s lav ox.txt`) mediante el script `run_pipeline_GO.py`.

### 4.1. Análisis del Barrido
El grid search de 180 combinaciones se guardó en `pipeline_results_GO.csv`. La muestra GO contiene un alto contenido de grupos oxigenados, lo que genera bandas de absorción extremadamente profundas.
- **Mejor Configuración por Penalización**: Se seleccionó **Moving_Average(7) + polynomial_baseline(deg=4)**. La presencia de deformaciones de línea base no lineales severas en el espectro del GO crudo requirió un ajuste polinomial de cuarto orden iterativo (IModPoly) para estimar el fondo sin distorsionar la región de huella dactilar.
- El gráfico de la mejor muestra GO se guardó como **`resultado_bestGO.png`** (con copia idéntica a **`resultado_best_GO.png`**).

### 4.2. Galería GO
Se extrajeron las configuraciones que lograron la máxima detección de grupos. El subgráfico se salvó como **`resultado_galeriaGO.png`** (con copia idéntica a **`resultado_galeria_GO.png`**).

---

## 5. Superposición y Comparación Química (Consigna 4.5)

El script `plot_superposition.py` generó el archivo **`resultado_superposicion_GO_rGO.png`**, el cual superpone los espectros corregidos óptimos de la muestra oxidada (GO, línea azul) y reducida (rGO, línea negra).

### 5.1. Análisis Químico del Proceso de Reducción
La superposición de los espectros permite comprobar mediante espectroscopía FTIR la efectividad del proceso de reducción del óxido de grafeno:

1. **Región O-H (~3400 cm⁻¹)**: El óxido de grafeno (GO) presenta una banda ancha y sumamente intensa atribuida al estiramiento de los grupos hidroxilo (-OH) y moléculas de agua intercaladas. Tras la reducción (rGO), esta banda experimenta una drástica disminución en su profundidad (aumento en transmitancia), confirmando la deshidratación y la eliminación de grupos hidroxilo del plano de grafeno.
2. **Región C=O (~1720 cm⁻¹)**: El pico correspondiente al estiramiento del carbonilo (C=O) en los grupos carboxilo y cetona en los bordes del GO disminuye notablemente en el rGO, lo cual evidencia la descomposición de los carboxilos.
3. **Región C=C (~1620 cm⁻¹)**: Esta banda corresponde a las vibraciones de estiramiento del esqueleto de carbono aromático $sp^2$. En el GO, este pico es visible pero a menudo solapado con la deformación del agua. En el rGO, la banda C=C se vuelve nítida y domina el espectro relativo, reflejando la restauración de la red conjugada de grafeno $sp^2$ tras la eliminación de los defectos de hibridación $sp^3$.
4. **Región C-O y C-O-C (~1400 y ~1050 cm⁻¹)**: Los picos asignados al estiramiento de enlaces C-O-C (epóxido) y C-O (alcóxido) son intensos en el GO debido a la oxidación del plano basal. En el espectro del rGO, estas bandas se reducen de forma significativa, indicando la deoxigenación casi completa de la estructura basal.

Este análisis espectroscópico corrobora de forma cuantitativa y cualitativa la transición estructural de un material altamente decorado con oxígeno (GO) hacia una red predominantemente grafénica (rGO).
