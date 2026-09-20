# FTIRdex

**FTIRdex** is a lightweight native desktop application designed for **FTIR spectroscopy analysis** (Fourier-transform infrared spectroscopy).

The application combines a high-performance native user interface written in C with a Python-based backend for numerical processing and plotting.

---

## Project Background

This project originally began as a gift for a former classmate, now a university faculty member and doctoral researcher at my institution, and for his laboratory.

After several weeks of development, the project was put on hold and remained unfinished. Rather than leaving the software unused, I decided to publish the project so that others can use it, improve it, or simply find it useful in their own FTIR-related work.

The project is released as a **work in progress**. Some components are incomplete, experimental, or still need cleanup and documentation.

---

## Main Features

* **Interactive Visualization**: Load and overlay multiple spectral samples simultaneously.
* **Signal Processing**: Apply smoothing and baseline-correction algorithms directly to loaded spectra.
* **Peak Identification**: Detect spectral peaks and valleys and associate them with corresponding functional groups.
* **Integrated CSV Table Viewer**: Inspect processed data in a built-in tabular view with scrolling and navigation.
* **Asynchronous Processing**: Keep the user interface responsive while analysis tasks are executed in separate threads.
* **Lightweight Design**: Minimal system resource usage compared with heavier scientific analysis environments.

---

## Project Structure

The repository is organized into a small native frontend, a Python analysis backend, and supporting libraries:

```text
FTIRdex/
├── FTIRdex/                   # Main C application and UI logic
│   ├── app_state.h/.c         # Application state and processing logic
│   ├── gui_render.h/.c        # UI rendering and drawing
│   ├── main.c                 # Application entry point and event loop
│   ├── iprocesses.h           # Asynchronous process execution API
│   ├── process_ftir.py        # Numerical analysis and plotting backend
│   ├── make_ico.py             # Local PNG-to-ICO icon generation script
│   └── resource.rc            # Windows resource definition
├── FTIRlib/                   # Core Python spectral-analysis library
├── libnativegui/              # Native GUI library Git submodule
├── libzipvfs/                 # Virtual filesystem library
├── Docs/                      # Project documentation
│   └── recuperacion-historica # Historical recovery material
├── CMakeLists.txt             # Cross-platform CMake build configuration
├── build.bat                  # Quick MSVC build script
├── installer.iss              # Inno Setup packaging script
├── assets/                    # Application graphics, fonts, and logos
├── LICENSE                    # Project licensing terms
├── CONTRIBUTING.md            # Contribution guidelines
├── TODO.md                    # Known issues and future work
└── README.md                  # Project documentation
```

---

## Requirements

The numerical backend requires **Python 3.9 or newer** together with the following packages:

```sh
pip install numpy scipy matplotlib pillow
```

For development and testing:

```sh
pip install pytest
```

At present, Python must be installed separately on the target system.

A future release may bundle a small Python distribution so that end users do not need to manage the Python runtime and dependencies manually.

---

## Building

### Method 1: CMake (Recommended)

The project uses **CMake** as its build system and is intended to support a modern cross-platform toolchain.

Configure the build directory:

```bash
cmake -B build -S .
```

Build the project in Release mode:

```bash
cmake --build build --config Release
```

The resulting executable and copied runtime resources will be placed under:

```text
build/Release/
```

### Method 2: MSVC (`build.bat`)

On Windows, the project can also be built directly from a **Visual Studio Developer Command Prompt** using the provided batch script:

```cmd
build.bat
```

This produces the `FTIRdex.exe` executable in the project root.

---

## Distribution and CI/CD

The repository includes an automated **GitHub Actions** workflow under:

```text
.github/workflows/build-and-release.yml
```

The workflow builds and packages the project for supported releases.

The generated artifacts include:

1. **Portable version**

   ```text
   FTIRdex-VERSION-portable.zip
   ```

   A standalone archive intended to run without a traditional installation process.

2. **Windows installer**

   ```text
   FTIRdex-VERSION-installer-x64.exe
   ```

   A standard Inno Setup installer for 64-bit Windows.

3. **Source package**

   ```text
   FTIRdex-VERSION-source.tar.gz
   ```

   A source archive for users who want to build the project manually on Linux/Unix systems with an X11 environment.

`VERSION` refers to the corresponding software release version.

---

## Project Status

FTIRdex is currently a **work in progress**.

Some parts of the repository reflect the project's history and were preserved because they may still be useful for future development. Other parts require cleanup, regeneration, restructuring, or additional documentation.

The current public release should therefore be considered a development snapshot rather than a finished scientific software package.

---

## TODO

### Documentation

* Clean up the documentation and rewrite the remaining Spanish material in English.
* Make English the main language for project documentation, development guidelines, and repository conventions.

### Codebase Cleanup

One of the main sources of technical debt in the current repository is that I originally overestimated how much programming and scripting the intended users would be comfortable maintaining themselves.

I assumed that their interest in advanced programming courses meant that they would be comfortable modifying and maintaining a codebase themselves. Because of that assumption, I did not establish proper version-control and repository-management practices from the beginning.

As a result, the repository contains some broken, experimental, or unrelated code that was accumulated during development. Some of these files need to be regenerated, cleaned up, reorganized, and properly referenced.

### Future Development

* Extend the software beyond FTIR spectroscopy and experiment with support for other spectrometric and spectroscopic techniques.
* Improve the architecture so additional analysis methods and instrument formats can be integrated more easily.
* Continue improving the standalone distribution so end users require fewer external dependencies.

---

## Licensing

FTIRdex is released under the **GNU General Public License v3.0 (GPLv3)**.

In simple terms, the software can be freely used, studied, modified, and redistributed, including for commercial purposes. Anyone may charge money for their own distribution or services based on the software.

When a modified version of FTIRdex is redistributed, the corresponding source code must remain available under the same GPLv3 freedoms. This means that modified versions cannot be redistributed as closed-source software under incompatible terms.

The project also contains components with their own licenses:

| Component      | License    | What you can do                                                                                                                                                              |
| -------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FTIRdex`      | **GPLv3**  | Use, modify, and redistribute it, including commercially. Modified versions that are redistributed must preserve the GPL freedoms and provide the corresponding source code. |
| `FTIRlib`      | **LGPLv3** | Use it as a library from software under other licenses, including proprietary software, subject to the LGPL terms.                                                           |
| `libnativegui` | **MIT**    | Use, modify, and redistribute it with very few restrictions, including in proprietary software. The original copyright and license notice must be retained.                  |
| `libzipvfs`    | **MIT**    | Use, modify, and redistribute it with very few restrictions, including in proprietary software. The original copyright and license notice must be retained.                  |

Please refer to the individual license files included with each component for the complete legal terms.


