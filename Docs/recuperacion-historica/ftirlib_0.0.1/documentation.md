# Documentación Técnica: Algoritmos de Procesamiento de Espectros FTIR

Este documento presenta la formulación matemática y el pseudocódigo en español de los algoritmos implementados en la biblioteca para el procesamiento de espectros de infrarrojo por transformada de Fourier (FTIR). Está diseñado para ingenieros de investigación y científicos que requieran rigor metodológico en la documentación de sus análisis.

---

## 1. Algoritmos de Suavizado (Smoothing)

El suavizado tiene como objetivo reducir el ruido de alta frecuencia (ruido instrumental y electrónico) sin distorsionar la forma ni la intensidad de las bandas de absorción reales.

### 1.1. Promedio Móvil (Moving Average)

#### Formulación Matemática
El filtro de promedio móvil reemplaza cada punto de la señal con el promedio aritmético de los puntos en una ventana simétrica de tamaño $W = 2k + 1$ centrado en dicho punto:

$$y_{\text{smooth}}[i] = \frac{1}{2k + 1} \sum_{j=-k}^{k} y[i + j]$$

Donde $y$ es la señal original de transmitancia y $k$ es el radio de la ventana. Para los extremos de la señal ($i < k$ o $i > N - 1 - k$), se aplica un acolchado por repetición del borde para evitar distorsiones o reducciones del tamaño del vector.

#### Pseudocódigo
```
Algoritmo Promedio_Movil
    Entrada: Señal y de longitud N, ancho de ventana W (debe ser impar)
    Salida: Señal suavizada y_smooth

    1. k = parte_entera(W / 2)
    2. Crear señal acolchada y_pad de longitud N + 2*k:
       y_pad[0 a k-1] = y[0]
       y_pad[k a N+k-1] = y
       y_pad[N+k a N+2*k-1] = y[N-1]
    3. Inicializar y_smooth de longitud N con ceros
    4. Para i desde 0 hasta N - 1 hacer:
       Suma = 0
       Para j desde -k hasta k hacer:
           Suma = Suma + y_pad[i + k + j]
       Fin Para
       y_smooth[i] = Suma / W
    5. Retornar y_smooth
Fin Algoritmo
```

---

### 1.2. Filtro de Savitzky-Golay

#### Formulación Matemática
El filtro de Savitzky-Golay suaviza los datos ajustando localmente un polinomio de grado $d$ mediante mínimos cuadrados sobre una ventana de tamaño $W = 2k + 1$:

Para cada punto $i$, se ajusta el polinomio:

$$p_i(z) = a_0 + a_1 z + a_2 z^2 + \dots + a_d z^d$$

Donde $z = -k, -k+1, \dots, k$ representa la posición local relativa al punto central. El valor suavizado es simplemente el término constante del ajuste polinomial:

$$y_{\text{smooth}}[i] = p_i(0) = a_0$$

Dado que este ajuste es lineal, se puede precalcular una matriz de coeficientes convolucionales $c_j$ que depende solo de $W$ y $d$:

$$y_{\text{smooth}}[i] = \sum_{j=-k}^{k} c_j y[i + j]$$

Los coeficientes se calculan mediante la pseudo-inversa de la matriz de Vandermonde local $J$:

$$C = (J^T J)^{-1} J^T$$
Donde $J_{z, m} = z^m$ para $z \in [-k, k]$ y $m \in [0, d]$. Los coeficientes de la fila correspondiente a la derivada de orden cero de $C$ corresponden a $c_j$.

#### Pseudocódigo
```
Algoritmo Savitzky_Golay
    Entrada: Señal y de longitud N, ancho de ventana W (impar), grado del polinomio d (d < W)
    Salida: Señal suavizada y_smooth

    1. k = parte_entera(W / 2)
    2. Construir la matriz de Vandermonde local J de tamaño (W x (d + 1)):
       Para cada fila z desde -k hasta k y columna m desde 0 hasta d:
           J[z + k, m] = z^m
    3. Calcular la pseudoinversa: C = (J^T * J)^(-1) * J^T
    4. Extraer los coeficientes de suavizado c (primera fila de C, correspondiente a m=0)
    5. Acolchar la señal y en los bordes usando simetría de espejo de longitud k.
    6. Inicializar y_smooth de longitud N
    7. Para i desde 0 hasta N - 1 hacer:
       y_smooth[i] = Suma(c[j + k] * y_pad[i + j + k]) para j desde -k hasta k
    8. Retornar y_smooth
Fin Algoritmo
```

---

### 1.3. Filtro de Mediana (Median Filter)

#### Formulación Matemática
Es un filtro no lineal que reemplaza cada punto por la mediana de los puntos dentro de una ventana de tamaño $W = 2k + 1$:

$$y_{\text{smooth}}[i] = \text{mediana}(\{y[i + j] \mid -k \le j \le k\})$$

Este filtro es extremadamente efectivo para remover ruido de tipo "sal y pimienta" (picos espurios o spikes muy delgados) sin distorsionar ni aplanar los bordes afilados de los picos verdaderos.

#### Pseudocódigo
```
Algoritmo Filtro_Mediana
    Entrada: Señal y de longitud N, ancho de ventana W (impar)
    Salida: Señal suavizada y_smooth

    1. k = parte_entera(W / 2)
    2. Inicializar y_smooth de longitud N
    3. Para i desde 0 hasta N - 1 hacer:
       - Extraer subvector ventana de tamaño W centrado en i:
         Si los índices caen fuera de [0, N-1], rellenar con el valor del borde.
       - Ordenar los elementos del subvector de menor a mayor.
       - y_smooth[i] = valor del elemento central en la lista ordenada (índice k)
    4. Retornar y_smooth
Fin Algoritmo
```

---

### 1.4. Filtro de Percentil (Percentile Filter)

#### Formulación Matemática
Es una generalización del filtro de mediana. Para cada ventana de tamaño $W = 2k + 1$ centrada en $i$, los valores se ordenan de menor a mayor y se selecciona el valor correspondiente al percentil $P$ (donde $P \in [0, 100]$):

$$y_{\text{smooth}}[i] = \text{Percentil}_P(\{y[i + j] \mid -k \le j \le k\})$$

Un percentil bajo (ej. 25%) tiende a seguir los mínimos locales, mientras que un percentil alto (ej. 75%) tiende a seguir los máximos locales.

#### Pseudocódigo
```
Algoritmo Filtro_Percentil
    Entrada: Señal y de longitud N, ancho de ventana W, percentil P (0 a 100)
    Salida: Señal filtrada y_smooth

    1. k = parte_entera(W / 2)
    2. Inicializar y_smooth de longitud N
    3. Para i desde 0 hasta N - 1 hacer:
       - Extraer subvector ventana de tamaño W centrado en i con manejo de bordes.
       - Ordenar los elementos del subvector de menor a mayor.
       - Indice_P = redondear( (P / 100) * (W - 1) )
       - y_smooth[i] = subvector_ordenado[Indice_P]
    4. Retornar y_smooth
Fin Algoritmo
```

---

## 2. Algoritmos de Corrección de Línea Base (Baseline Correction)

La línea base en espectroscopía representa la deriva de la señal de fondo debido a dispersión física de la luz, absorción del soporte o inestabilidad de la fuente analítica. Su remoción es crítica para cuantificar la intensidad real de las bandas.

En transmitancia, dado que la corrección física debe ser multiplicativa ($T_{\text{corregida}} = \frac{T_{\text{medida}}}{T_{\text{línea base}}} \times 100$), primero estimamos la envolvente superior $z$ (que actúa como línea base en transmitancia) y luego aplicamos la división.

---

### 2.1. Eliminación de Tendencia Lineal (Detrend)

#### Formulación Matemática
Ajusta una línea recta $z_i = m x_i + b$ a todo el espectro mediante mínimos cuadrados ordinarios y la sustrae:

$$m = \frac{N \sum x_i y_i - \sum x_i \sum y_i}{N \sum x_i^2 - (\sum x_i)^2}, \quad b = \frac{\sum y_i - m \sum x_i}{N}$$

El espectro corregido de forma aditiva se calcula como $y_{\text{corr}} = y - z + \bar{y}$.

#### Pseudocódigo
```
Algoritmo Detrend_Lineal
    Entrada: Vector x (número de onda), Vector y (transmitancia) de longitud N
    Salida: Señal corregida y_corr

    1. Calcular las sumatorias: Sum_x, Sum_y, Sum_xy, Sum_x2 de los elementos.
    2. m = (N * Sum_xy - Sum_x * Sum_y) / (N * Sum_x2 - (Sum_x)^2)
    3. b = (Sum_y - m * Sum_x) / N
    4. Calcular la línea base: z = m * x + b
    5. y_corr = y - z + promedio(y)
    6. Retornar y_corr
Fin Algoritmo
```

---

### 2.2. Línea Base Lineal Extrema (Linear Baseline)

#### Formulación Matemática
Conecta de forma directa el primer punto $(x_0, y_0)$ y el último punto $(x_{N-1}, y_{N-1})$ del espectro con un segmento de recta, sustrayéndola posteriormente:

$$z_i = y_0 + \frac{y_{N-1} - y_0}{x_{N-1} - x_0} (x_i - x_0)$$

#### Pseudocódigo
```
Algoritmo Linea_Base_Extrema
    Entrada: Vector x, Vector y de longitud N
    Salida: Señal corregida y_corr

    1. x0 = x[0], y0 = y[0]
    2. xN = x[N-1], yN = y[N-1]
    3. Inicializar z de longitud N
    4. Para i desde 0 hasta N - 1 hacer:
           z[i] = y0 + (yN - y0) * (x[i] - x0) / (xN - x0)
    5. y_corr = y - z + promedio(y)
    6. Retornar y_corr
Fin Algoritmo
```

---

### 2.3. Ajuste Polinomial Iterativo Modificado (IModPoly)

#### Formulación Matemática
Propuesto por Lieber et al., ajusta iterativamente un polinomio $z(x) = \sum_{j=0}^d a_j x^j$ de grado $d$. Si los datos de transmitancia caen por debajo del polinomio ajustado (lo que indica la presencia de una banda de absorción), estos valores se reemplazan temporalmente por el valor del polinomio en esa iteración más el umbral del ruido $\sigma$ (desviación estándar de los residuos). Esto evita que el polinomio sea arrastrado hacia abajo por los picos.

Para cada iteración $t$:
1. Ajustar el polinomio $P_t(x)$ a los datos modificados $y^{(t-1)}$.
2. Calcular los residuos $r_i = y_i - P_t(x_i)$ y su desviación estándar $\sigma$.
3. Actualizar los datos modificados:
   $$y^{(t)}[i] = \begin{cases} P_t(x_i) & \text{si } y_i < P_t(x_i) - \sigma \quad (\text{en transmitancia}) \\ y_i & \text{de lo contrario} \end{cases}$$

#### Pseudocódigo
```
Algoritmo IModPoly
    Entrada: Vector x, Vector y, grado d, iteraciones MaxIter
    Salida: Línea base estimada z

    1. y_base = copiar(y)
    2. Para iter desde 1 hasta MaxIter hacer:
       - Ajustar polinomio de grado d a (x, y_base) para obtener coeficientes 'coefs'
       - Evaluar polinomio: z = evaluar(coefs, x)
       - Calcular sigma = desv_estandar(y - z)
       - Para i desde 0 hasta N - 1 hacer:
             Si y[i] < z[i] - sigma entonces:  (En transmitancia los picos van hacia abajo)
                 y_base[i] = z[i]
             Sino:
                 y_base[i] = y[i]
             Fin Si
       - Si coefs no cambian significativamente con respecto a la iteración anterior, romper ciclo.
    3. Retornar z obtenido con los últimos coeficientes
Fin Algoritmo
```

---

### 2.4. Mínimos Cuadrados Asimétricos (Asymmetric Least Squares - AsLS)

#### Formulación Matemática
Introducido por Paul Eilers (2003). Resuelve un problema de optimización de mínimos cuadrados penalizados:

$$\min_{z} \sum_{i=1}^N w_i (y_i - z_i)^2 + \lambda \sum_{i=3}^N (\Delta^2 z_i)^2$$

Donde:
- $y$ es la señal medida y $z$ es la línea base estimada.
- $\lambda$ es el parámetro de suavizado (regularización de Tikhonov sobre la segunda derivada).
- $\Delta^2 z_i = z_i - 2z_{i-1} + z_{i-2}$ es el operador de segunda diferencia.
- $w_i$ son los pesos asimétricos definidos de forma iterativa:

$$w_i = \begin{cases} p & \text{si } y_i < z_i \quad (\text{punto dentro de un pico de transmitancia}) \\ 1 - p & \text{si } y_i \ge z_i \quad (\text{punto de línea base}) \end{cases}$$

Típicamente, el parámetro de asimetría $p$ se fija en un valor muy pequeño (ej. $10^{-3}$), lo que permite que el ajuste ignore los picos hacia abajo y pase justo por la parte superior del espectro de transmitancia.

En forma matricial, se resuelve el sistema lineal disperso:

$$(W + \lambda D^T D) z = W y$$

Donde $W = \text{diag}(w)$ y $D$ es la matriz de segunda diferencia de tamaño $(N-2) \times N$.

#### Pseudocódigo
```
Algoritmo AsLS
    Entrada: Vector y de longitud N, suavizado lam, asimetría p, iteraciones MaxIter
    Salida: Línea base estimada z

    1. Construir matriz dispersa de diferencias D2 de tamaño (N-2) x N con patrón [1, -2, 1]
    2. D = D2^T * D2 (matriz dispersa simétrica de tamaño N x N)
    3. Inicializar pesos w = vector de unos de longitud N
    4. Inicializar z de longitud N
    5. Para iter desde 1 hasta MaxIter hacer:
       - W = matriz diagonal dispersa con los elementos de w
       - Resolver sistema lineal: A = W + lam * D,  A * z = w * y
       - Para i desde 0 hasta N - 1 hacer:
             Si y[i] < z[i] entonces:
                 w[i] = p
             Sino:
                 w[i] = 1 - p
             Fin Si
    6. Retornar z
Fin Algoritmo
```

---

### 2.5. Mínimos Cuadrados Penalizados Adaptativos con Pesos Iterativos (airPLS)

#### Formulación Matemática
Desarrollado por Zhang et al. (2010), airPLS ajusta la línea base sin necesidad de un parámetro de asimetría $p$ prefijado. En su lugar, el algoritmo actualiza los pesos de forma adaptativa y exponencial en función de la distancia entre la señal y la línea base en cada iteración.

Si en la iteración $t$ definimos el error residual como $d_i = y_i - z_i$, los pesos se actualizan como:

$$w_i = \begin{cases} 0 & \text{si } y_i \ge z_i \quad (\text{puntos de picos en absorbancia}) \\ \exp\left( \frac{t \cdot (y_i - z_i)}{\text{std}(d^-)} \right) & \text{si } y_i < z_i \quad (\text{puntos bajo la línea base}) \end{cases}$$

Donde $d^-$ es el subvector que contiene únicamente los residuos negativos de la iteración.

Para aplicar airPLS a transmitancia, primero invertimos el espectro: $y_{\text{inv}} = \max(y) - y$. Así, los picos de transmitancia apuntan hacia arriba y se comportan matemáticamente como picos de absorbancia. Tras estimar la línea base en el espacio invertido ($z_{\text{inv}}$), la regresamos al espacio original mediante $z = \max(y) - z_{\text{inv}}$.

#### Pseudocódigo
```
Algoritmo airPLS
    Entrada: Vector y de longitud N, suavizado lam, iteraciones MaxIter, tolerancia tol
    Salida: Línea base estimada z

    1. Determinar el máximo: y_max = maximo(y)
    2. Invertir la señal: y_inv = y_max - y
    3. Construir D = D2^T * D2 como en AsLS
    4. Inicializar pesos w = vector de unos de longitud N
    5. Inicializar z_inv de longitud N
    6. Para t desde 1 hasta MaxIter hacer:
       - W = diag(w)
       - Resolver (W + lam * D) * z_inv = w * y_inv
       - d = y_inv - z_inv
       - Extraer subvector d_neg conteniendo los elementos de d que sean < 0
       - Si d_neg está vacío, romper ciclo.
       - std_neg = desviacion_estandar(d_neg)
       - Si std_neg < tol, romper ciclo.
       - Para i desde 0 hasta N - 1 hacer:
             Si d[i] < 0 entonces:
                 w[i] = exp( t * d[i] / std_neg )
             Sino:
                 w[i] = 0
             Fin Si
    7. z = y_max - z_inv
    8. Retornar z
Fin Algoritmo
```

---

### 2.6. Mínimos Cuadrados Penalizados con Pesos Asimétricos Locales (arPLS)

#### Formulación Matemática
Propuesto por Baek et al. (2015), arPLS utiliza una función logística suave para actualizar los pesos, permitiendo que la señal de ruido en la línea base tenga una transición continua hacia la región del pico, mejorando enormemente la estabilidad matemática del ajuste ante ruido severo.

Si $d_i = y_i - z_i$ representa la diferencia entre la señal y la línea base calculada, los pesos de arPLS en la iteración $t$ se calculan como:

$$w_i = \frac{1}{1 + \exp\left( \frac{d_i - (2 \sigma^- + \mu^-)}{\sigma^-} \right)}$$

Donde:
- $\mu^-$ es el valor medio de las diferencias negativas ($d_i < 0$).
- $\sigma^-$ es la desviación estándar de las diferencias negativas ($d_i < 0$).

Al igual que con airPLS, para espectros de transmitancia se realiza la inversión de la señal antes de ejecutar el algoritmo y se revierte la línea base final al espacio de transmitancia.

#### Pseudocódigo
```
Algoritmo arPLS
    Entrada: Vector y de longitud N, suavizado lam, iteraciones MaxIter, tolerancia tol
    Salida: Línea base estimada z

    1. y_max = maximo(y)
    2. y_inv = y_max - y
    3. Construir D = D2^T * D2 como en AsLS
    4. Inicializar pesos w = vector de unos de longitud N
    5. Para iter desde 1 hasta MaxIter hacer:
       - W = diag(w)
       - Resolver (W + lam * D) * z_inv = w * y_inv
       - d = y_inv - z_inv
       - Extraer subvector d_neg de elementos d < 0
       - Si d_neg está vacío:
             mean_neg = 0.0
             std_neg = desviacion_estandar(d)
         Sino:
             mean_neg = promedio(d_neg)
             std_neg = desviacion_estandar(d_neg)
         Fin Si
       - Si std_neg < tol, romper ciclo.
       - Para i desde 0 hasta N - 1 hacer:
             exponente = (d[i] - (2 * std_neg + mean_neg)) / std_neg
             exponente = limitar_entre_valores(exponente, -50, 50)
             w[i] = 1.0 / (1.0 + exp(exponente))
    6. z = y_max - z_inv
    7. Retornar z
Fin Algoritmo
```

---

## 3. Detección de Picos y Asignación

### 3.1. Inversión y Detección de Mínimos Locales
Las bandas de FTIR se registran como caídas (mínimos locales) en la transmitancia. El algoritmo realiza la inversión del espectro corregido:

$$y_{\text{inv}}[i] = 100.0 - y_{\text{corr}}[i]$$

Sobre $y_{\text{inv}}$ se ejecuta la detección de picos (máximos locales) evaluando dos criterios críticos para rechazar ruido instrumental residual:
1. **Prominencia del Pico**: La altura vertical de la punta del pico con respecto al fondo local del valle más alto a la izquierda o derecha del mismo. Se establece un umbral mínimo $P_{\text{min}}$ (por defecto $0.8\%$).
2. **Distancia Mínima**: La separación mínima en número de canales (puntos) entre dos picos adyacentes para evitar el sobredireccionamiento de hombros de picos. Se establece un umbral mínimo $D_{\text{min}}$ (por defecto $15$ puntos, equivalente a $\approx 30\text{ cm}^{-1}$).

---

### 3.2. Asignación de Grupos Funcionales
Cada pico detectado en la longitud de onda $x_p$ se compara con la base de conocimiento estructurada de rangos definidos para óxidos de grafeno:

| Grupo Funcional | Rango de Número de Onda ($cm^{-1}$) | Significado Químico |
| :--- | :--- | :--- |
| **O-H** | $[3200, 3600]$ | Estiramiento O-H (alcohol, fenol, agua adsorbida) |
| **C-H** | $[2800, 3000]$ | Estiramiento C-H alifático ($sp^3$) |
| **CO2** | $[2300, 2400]$ | Dióxido de carbono atmosférico residual |
| **C=O** | $[1650, 1750]$ | Estiramiento C=O de carbonilos / carboxilos |
| **C=C** | $[1500, 1650]$ | Estiramiento C=C del plano aromático de grafeno $sp^2$ |
| **C-O** | $[1250, 1450]$ | Estiramiento C-O carboxílico / deformación C-OH |
| **C-O-C** | $[950, 1250]$ | Estiramiento C-O-C del grupo epoxi / alcoxi |

Un pico $x_p$ es **Válido** si existe al menos un grupo funcional $g$ tal que $W_{g,\text{min}} \le x_p \le W_{g,\text{max}}$. En caso contrario, se reporta como un pico de **Ruido**.
