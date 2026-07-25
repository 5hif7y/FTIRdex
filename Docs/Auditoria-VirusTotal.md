
# Auditoria de seguridad y falsos positivos

Tras auditar el código fuente del proyecto, el compilado y eel comportamiento en tiempo de ejecucion, se detecta la raíz del problema de los avisos en VirusTotal.

Las detecciones observadas `Wacatac.B!ml`, `Win.Trojan.Gen`, `Trojan.Malware.300983.susgen`,
son falsos positivos generados por algoritmos de Inteligencia Artificial de los motores antivirus. Estos motores marcan el software basándose en **comportamientos "sospechosos"**, y en la falta de **reputación** y **certificados**, no porque contengan código vulnerable real.

> ![NOTA] 
> En el Link Reportado en la entrega de la version **0.0.5**.
> https://www.virustotal.com/gui/file/f6e0e56c446018427efeee316b8a1b7be0fe3e6021304ff23b37811aac36c868?nocache=1
> Se revocaron `Win.Trojan.Gen` de Webroot y `Trojan.Malware.300983.susgen` de MaxSecure
Se agrego `BehavesLike.Win32.ObfuscatedPoly.vc` de SkyHigh
`Wacatac.B!ml` de Microsoft se mantiene igual

## Causas principales del Falso Positivo 

La arquitectura actual de FTIRdex tiene una combinación de características que disparan las heurísticas de los antivirus:

### 1. Invocación directa de procesos

En el archivo `FTIRdex/iprocesses.h`, el programa utiliza la API de Windows `CreateProcessW` para llamar a Python de la siguiente manera:

```sh
BOOL success = CreateProcessW(..., CREATE_NO_WINDOW, ...);
```

Esto alerta a los algoritmos de IA autimaticos, por lanzar intérpretes de comandos de manera oculta y directa, es exactamente la misma técnica que utiliza un malware para ejecutar scripts maliciosos en segundo plato sin que el usuario se dé cuenta. Esto no significa que este mal implementado, solo que esta gente tiene la politica de "primero retener, luego preguntar" cosa que no esta mal en la practica hoy en dia. De todas maneras pasameros a usar la libreria oficial de Python para minimizar esta advertencia.

### 2. Faltan metadatos

Al inspeccionar `FTIRdex/resource.rc`, el archivo solo contiene el ícono:

```C 
ICON DISCARDABLE "../assets/icon.ico"
```

Esto alerta a la detección automatica, porque el ejecutable `FTIRdex.exe` resultante, no tiene información de versión `VS_VERSION_INFO`. Carece de nombre de compañia, copyright, nombre del producto o versión. La mayoria del software legitimo tiene estos metadatos, por lo la ausencia de estos reduce drácticamente el puntaje de confianza `Trus Score` en Windows Defender.

### 3. Falta de firma digital (`Authenticode`)

El instalador y ejecutable no están firmados criptográficamente por una Autoridad Certificadora (`CA`). Para Windows, FTIRdex es un programa anónimo de origen desconocido.

### 4. Actividad del sistema de archivos (`libzipvfs`)

FTIRdex extrae archivos `.ftirzip` y crea archivos temporales. Un ejecutable anónimo y sin metadatos que invoca procesos ocultos y escribe archivos en el disco es marcado inmediatamente.

## Soluciones

### 1. Inplementaciones inmediatas

1. **Agregar `VS_VERSION_INFO` en el archivo `resource.rc`**; agregar más metadatos elevaria muchísimo la legitimidad del archivo.

2. **Hacer los tramites de *Falso Positivo* a Microsoft**: Subir el archivo al portal de *Microsoft Security Intelligence*, marcándolo como "Incorrectly detected". Microsoft lo analiza manualmente y lo añade a su lista blanca en pocas horas, limpiando el aviso de `Wacatac.B!ml` globalmente.

### 2. Soluciones de arquitectura 

**Migrar a la API C de Python `Python.h`**: Se intuye que llamar a `python.exe` de manera directa es la raiz del problema conductual. La minimizacion de esta problematica es vincular la librería oficial de Python directamente a C e invocar el intérprete embebido en lugar de usar `CreateProcessW`, en su lugar se usaria `PyRun_SimpleString()`, o importaciones a nivel binario. Esto elimina el comportamiento sospechoso de "spawning" y tambien aumenta enormemente el rendimiento.

### 3. Soluciones comerciales

**Adquirir un cerfificado Code Signing** (`Authenticode`), comprar un certificado a nombre de alguien, el laboratorio o la institucion, aproximadamente 80-100 USD al año, y firmar tanto ejecutable e instalador con `signtool.exe`. Garantizaria que el software nunca mas sea malinterpretado por las heurísticas automaticas.




---------


Un **bypass** a estos problemas generar los ejecutables con los servidores de Github

Parece que se detecta una sospecha de malware al compilar el maquinas personales.

Esto no ocurre si se usa 'Github'/Servidor/Maquina con más autoridad y credibilidad.

De todas maneras para disminuir las problematicas de seguridad 

Si empieza a ocurrir con el ejecutable compilado por Github o si se requiere una solucion comercial directa, hay que hacer los tramites:

https://www.microsoft.com/en-us/wdsi/filesubmission

https://learn.microsoft.com/es-es/unified-secops/submission-guide

Este repositorio contiene la lista de tramites de manera mas completa:

https://github.com/hankhank10/false-positive-malware-reporting




