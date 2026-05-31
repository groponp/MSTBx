# MSTBx (Molecular Simulation ToolBox) v0.8.0

**MSTBx** es un ecosistema modular de Python diseñado para simplificar la preparación, generación de archivos de configuración y traducción de simulaciones de Dinámica Molecular (MD). Está optimizado para sistemas de gran escala (millones de átomos) y soporta flujos de trabajo multilingües.

---

## 🚀 Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/groponp/MSTBx.git
cd MSTBx/

# 2. Configurar entorno Conda (Linux/Mac)
conda env update -f mstbx.yml
conda activate mstbx

# 3. Instalar en modo editable
pip install -e .
```

### Habilitar Autocompletado (TAB)
```bash
# Bash: echo 'eval "$(_MSTBX_COMPLETE=bash_source mstbx)"' >> ~/.bashrc
# Zsh: echo 'eval "$(_MSTBX_COMPLETE=zsh_source mstbx)"' >> ~/.zshrc
```

---

## 🛠️ Módulos de Construcción (Topology)

### 1. `topopsfgen` (CHARMM/NAMD)
Generación de archivos PSF/PDB con control granular de padding.
Uso: `mstbx topopsfgen --env [solution|membrane|smd] [OPCIONES]`

*   **Sistemas en Solución**:
    `mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --salt 0.150`
*   **Sistemas de Membrana**:
    `mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --salt 0.150`
*   **Sistemas SMD**:
    `mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --salt 0.150 --atoms-pull "resid 100" --atoms-anchor "resid 1"`

### 2. `topotleap` (AMBER)
Generación de archivos PRMTOP/INPCRD usando tLeap (En desarrollo).

---

## ⚙️ Módulos de Simulación (Inputs)

Generación de protocolos de simulación con soporte multi-motor (`--engine namd|amber|gmx`).

*   **`md-inputs`**: Dinámica estándar (NVT, NPT, Producción).
    `mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb`
*   **`smd-inputs`**: Dinámica de estiramiento (SMD).
    `mstbx smd-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --selpull "resid 100" --target-center 50`
*   **`metad-inputs`**: Metadinámica Well-Tempered.
    `mstbx metad-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --sel1 "segid PROA"`

---

## 🧪 Herramientas Avanzadas

*   **`pdbwriter`**: Reparación inteligente de PDBs (solo gaps internos), detección de puentes S-S y protonación.
*   **`md-translate`**: Traducción de trayectorias y coordenadas entre motores (ej. NAMD a GROMACS).
*   **`colabfold`**: Predicción de estructuras mediante Apptainer.
*   **`mkdocking-cmplx`**: Generación de complejos proteína-ligando a partir de docking.

---

## 📚 Documentación y Wiki
MSTBx cuenta con una Wiki multilingüe detallada en `docs/wiki/`:
*   🇺🇸 [English Documentation](docs/wiki/en/Home.md)
*   🇪🇸 [Documentación en Español](docs/wiki/es/Home.md)
*   🇧🇷 [Documentação em Português](docs/wiki/pt/Home.md)

Para una guía paso a paso de pruebas, consulta: [**Testing_Manual.md**](docs/Testing_Manual.md).

---

## 🔄 Versiones y Actualización
MSTBx utiliza un esquema de versionado estable. La rama actual es la **v0.8.0**. Las actualizaciones seguirán el patrón `0.8.x` hasta `0.8.20` antes de pasar a la `0.9.0`.

```bash
# Para actualizar a la última versión del código
pip install --upgrade -e .
```
