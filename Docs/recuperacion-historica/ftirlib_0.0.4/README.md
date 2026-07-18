# FTIR Analysis Library

Biblioteca avanzada para preprocesamiento, corrección de línea base y detección automática de grupos funcionales en espectros FTIR de Óxido de Grafeno (GO) y Óxido de Grafeno Reducido (rGO).

## Instalación y Actualización

La biblioteca se distribuye en formato ZIP (`ftirlib.zip`) conteniendo el paquete de código fuente, los scripts de ejemplo y los reportes de desarrollo.

### Instalación Inicial
Para instalar la biblioteca y todas sus dependencias automáticamente, ejecute en la terminal desde el directorio donde se ubica el archivo `.zip`:

```bash
pip install ftirlib.zip
```

### Actualización o Reinstalación
Si recibe una nueva versión de la biblioteca con el mismo nombre y desea actualizarla, ejecute:

```bash
pip install --force-reinstall ftirlib.zip
```

## Uso Rápido

```python
from ftir_library import load_ftir_data, transmittance_to_absorbance, correct_baseline_absorbance

# Cargar datos
x, y_trans = load_ftir_data("GO coque s lav red.txt")

# Convertir a absorbancia
y_abs = transmittance_to_absorbance(y_trans)

# Corregir linea base usando arPLS
z, y_corr = correct_baseline_absorbance(x, y_abs, method="arpls", lam=1e5)
```

## Estructura del Repositorio

- `src/ftir_library/`: Código fuente de la biblioteca Python.
- `docs/`: Documentación teórica, reportes en markdown e informe formal en LaTeX (`informe_desarrollo.tex`).
- `examples/`: Datos FTIR experimentales y scripts ejecutables (`run_pipeline_absorbance.py`, `plot_superposition_absorbance.py`, `generate_reports.py`).

## Historial de versiones

* [13/06/2026] – v0.0.3 (actual): prototipo de librería adaptado al uso profesional (Informe_Tecnico_FTIR_alpha-0.0.3.pdf / ftirlib_0.0.3.zip)
* [09/06/2026] – v0.0.2: prototipo de librería (Informe_Tecnico_FTIR_alpha-0.0.2.pdf / ftirlib_0.0.2.zip)
* [08/06/2026] – v0.0.1: versión experimental inicial (Informe_Tecnico_Informal.pdf / entregar-FTIR-alpha-0.0.1.zip)

## Tareas previstas para la próxima versión

1. Refinar la documentación técnica para adoptar un estilo más objetivo y orientado a ingeniería.
2. Incorporar nuevos algoritmos de suavizado y corrección de línea base.
3. Implementar un sistema manual simplificado de configuración de algoritmos.
4. Incorporar algoritmos de atenuación y amplificación selectiva de bandas espectrales.
5. Desarrollar un módulo OCR/CV basado en C++ y OpenCV accesible desde Python.
6. Mejorar la validación experimental, la correlación entre matemáticas y algoritmos, y la descripción de la arquitectura de la biblioteca.
7. Documentar formalmente la evolución entre versiones mediante un changelog incluido en la documentacion.
8. Realizar limpieza y reorganización de los scripts de ejemplo.
9. Pruebas automatizadas de calidad

## Licencia

Uso interno estrictamente confidencial. Copyright (C) 2026 Matías Roberto Alemán.
