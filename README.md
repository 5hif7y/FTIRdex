# FTIRdex

**FTIRdex** es una aplicación de escritorio nativa y liviana diseñada para el **análisis espectroscópico FTIR** (Infrarrojo por Transformada de Fourier). 

La aplicación combina una interfaz de usuario nativa de alto rendimiento desarrollada en C con un potente motor de procesamiento numérico y graficación basado en Python.

---

## Características Principales

* **Visualización en Tiempo Real**: Carga y superposición simultánea de múltiples muestras espectrales.
* **Procesamiento de Señal**: Algoritmos de suavizado (Smooth) y corrección de línea base (Baseline) aplicados al instante.
* **Identificación de Picos**: Detección inteligente de picos y valles espectrales asignando automáticamente sus grupos funcionales.
* **Visor de tabla CSV Integrado**: Reporte tabular en tiempo real con opción de navegación y scroll dinámico.
* **Hilos de Ejecución Asíncronos**: Interfaz fluida sin congelamientos gracias al procesamiento asíncrono multiplataforma.
* **Diseño Ultra Ligero**: Consumo mínimo de recursos del sistema.

---

## Estructura del Proyecto

El repositorio está organizado de forma limpia y simplificada:

```sh
FTIRdex/
├── FTIRdex/                   # Código fuente en C (interfaz y lógica de procesos)
│   ├── app_state.h/.c         # Gestión de datos y lógica de ejecución
│   ├── gui_render.h/.c        # Renderizado y dibujo UI
│   ├── main.c                 # Punto de entrada y bucle de eventos
│   ├── iprocesses.h           # API de ejecución de subprocesos asíncronos
│   ├── process_ftir.py        # Backend de análisis numérico y matplotlib
│   ├── make_ico.py            # Script regenerador del icono local (.png a .ico)
│   └── resource.rc            # Archivo de recursos de Windows para el icono
├── FTIRlib/                   # Biblioteca núcleo de análisis espectral en Python
│   └── recuperacion-historica # Carpeta de recuperación de entregas anteriores
├── libnativegui/              # Submódulo Git de la librería gráfica nativa
├── Docs/                      # Manuales y documentación del proyecto
├── CMakeLists.txt             # Configuración del sistema de construcción CMake
├── build.bat                  # Script de compilación rápida para MSVC
├── installer.iss              # Script de empaquetado para Inno Setup
├── Icono.png/.ico/.Aseprite   # Elementos gráficos y logos del programa
├── LICENSE                    # Declaración de términos de licencia comercial
└── README.md                  # Esta documentación
```

---

## Requisitos de Ejecución

El backend numérico requiere una instalación de **Python (3.9 o superior)** con las siguientes librerías de análisis científico:

```bash
pip install numpy scipy matplotlib pillow pytest
```
Pero se planea embeber una pequeña distribución Python que no requiera atención extra del usuario en el futuro

---

## Instrucciones de Compilación y Construcción

### Método 1: Compilación Moderna con CMake (Recomendado)
El proyecto utiliza CMake como sistema de construcción multiplataforma. Genera automáticamente los ejecutables y copia todos los archivos auxiliares necesarios (los scripts de Python, la carpeta `FTIRlib` y el icono) a la carpeta de salida.

```bash
# 1. Configurar el directorio de construcción
cmake -B build -S .

# 2. Compilar el proyecto en modo optimizado (Release)
cmake --build build --config Release
```
*El ejecutable final y sus recursos listos para entregar se ubicarán en `build/Release/`.*

### Método 2: Compilación Clásica con MSVC (`build.bat`)
Si utiliza el toolchain nativo de Visual Studio en Windows (Developer Command Prompt), se puede compilar de forma rápida ejecutando el archivo batch en la raíz:

```cmd
build.bat
```
*Esto generará el archivo `FTIRdex.exe` directamente en la raíz de tu proyecto.*

---

## Distribución y CI/CD

El proyecto incluye un flujo de integración y entrega continua (CI/CD) automatizado a través de **GitHub Actions** (`.github/workflows/build-and-release.yml`). En cada confirmación a la rama `main` o al crear una etiqueta de versión (`v*`), el servidor compila y empaqueta de forma automática los siguientes entregables:

1. **Versión Portable (`FTIRdex-portable.zip`)**: Un archivo comprimido listo para usar sin instalación previa.
2. **Instalador de Windows (`FTIRdex-Installer-x64.exe`)**: Un instalador guiado estándar creado con Inno Setup que añade accesos directos al escritorio.
3. **Código Fuente (`FTIRdex-source.tar.gz`)**: Tarball para entornos Linux/Unix donde los usuarios finales deseen compilar la aplicación utilizando el servidor gráfico X11.

---

## Licencia

  1. Este software es propiedad comercial y propietaria de Ing. Mendoza Pablo Nicolás. Todos los derechos reservados.

  2. El uso del código de la interfaz gráfica nativa se rige bajo la licencia **MIT** provista dentro de la subcarpeta `libnativegui`. La cual es una licencia libre para todo, que solo requiere referenciar el nombre o alias del autor.


