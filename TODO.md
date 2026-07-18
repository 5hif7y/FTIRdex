To do

1. Extender FTIRdex:

  1.1. **Agregar** soporte de temas personalizables en un archivo `.ini` (actualmente solo uno *hardcodeado*, con modo oscuro y claro)

  1.2. **Auditar**: Algunos strings sobresalen de su cuadro, como "Visor CSV - Muestra 1/1"

  1.3. **Embeber** un interprete Python en la aplicación

  1.4. **Extender** el `UCRT` para soportar entre Windows XP y Windows 11, tal vez requiera crear `libeucrt`

  1.5. **Crear** una librería externa para normalizar la renderización de imágenes e independizarla de `gdi32`/`X11`, tal vez `libiren`
  
  1.6. **Auditar**: Algunas imágenes sufren compresión horizontal, la cual reduce o borra la visibilidad de las lineas de marcado de grupos funcionales de los gráficos en el modo normal


2. Extender FTIRlib:

  2.1. **Añadir** más algoritmos de suavizado y corrección de línea base

  2.2. **Añadir** algoritmos de ampliación y atenuación de picos.

  2.3. **Añadir** Modulo C++ OR/CV para generar muestras desde imágenes, accesible desde Python

