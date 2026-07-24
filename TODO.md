# To do

## 1. Extender FTIRdex:

  1.1. **Agregar** soporte de temas personalizables en un archivo `.ini` (actualmente solo uno *hardcodeado*, con modo oscuro y claro)

  1.2. **Auditar**: Algunos strings sobresalen de su cuadro, como "Visor CSV - Muestra 1/1"

  1.3. **Embeber** un interprete Python en la aplicación

  1.4. **Extender** el `UCRT` para soportar entre Windows XP y Windows 11, tal vez requiera crear `libeucrt`

  1.5. **Crear** una librería externa para normalizar la renderización de imágenes e independizarla de `gdi32`/`X11`, tal vez `libiren`
  
  1.6. **Auditar**: Algunas imágenes sufren compresión horizontal, la cual reduce o borra la visibilidad de las lineas de marcado de grupos funcionales de los gráficos en el modo normal

  1.7 **Auditar**: VirusTotal arroja advertencias de seguridad, tal vez sea porque no usamos la libreria oficial de Python o por no usar la compilacion directa de Github, investigar

  1.8 **Auditar**: Agregar testing para lenguaje C

  1.9 **Auditar**: Revisar el algoritmo de separación de etiquetas de grupos funcionales, del modo de marcado 'Lineas Completas'.


## 2. Extender FTIRlib:

  2.1. **Añadir** más algoritmos de suavizado y corrección de línea base

  2.2. **Añadir** algoritmos de ampliación y atenuación de picos.

  2.3. **Añadir** Modulo C++ OR/CV para generar muestras desde imágenes, accesible desde Python


## 3. Extender documentación:

  3.1 Manual de FTIRdex (manual simple de la interfaz y uso de la aplicación)

  3.2 Manual de FTIRlib (manual de la librería para manipular manualmente las muestras)

  3.3 Informe Ejecutivo (informe del proyecto resumido)

  3.4 Informe Técnico (informe del proyecto al detalle)

  3.5 Documentación de especificación (este es de carácter confidencial, transparenta todo el proyecto para que un Junior lo pueda relevar)

