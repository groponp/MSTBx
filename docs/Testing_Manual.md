# 🧪 MSTBx v0.8.0: Guía de Pruebas y Depuración

Esta guía te permitirá validar cada módulo de la nueva arquitectura modular.

---

## 1. Módulos de Construcción (`topopsfgen`)

### 1.1 Solución (Standard)
```bash
mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --padding 18 --salt 0.150
```
*   **Check:** Verifica que `01build/step3_pbcsetup.str` tenga dimensiones consistentes con la proteína + 36A (18 de cada lado).

### 1.2 Membrana
```bash
mstbx topopsfgen --env membrane --psf lipids.psf --pdb lipids.pdb --padding 15 --z-dist 10 --salt 0.150
```
*   **Check:** Verifica que las aguas se hayan eliminado correctamente de la zona hidrofóbica.

### 1.3 SMD (Orientado)
```bash
mstbx topopsfgen --env smd --psf prot.psf --pdb prot.pdb --atoms-anchor "resid 1" --atoms-pull "resid 100" --extra-space 60 --salt 0.150
```
*   **Check:** El eje Z de la caja debe ser significativamente más largo que X e Y.

---

## 2. Módulos de Simulación (`inputs`)

### 2.1 MD Estándar
```bash
mstbx md-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 5.0
```
*   **Nota:** `--dcdfreq 5.0` ahora se interpreta como **5 picosegundos**.

### 2.2 Steered MD
```bash
mstbx smd-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "resid 100" --selanchor "resid 1" --target-center 50
```

### 2.3 Metadinámica
```bash
mstbx metad-inputs --engine namd --env solution --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB" --target-distance 60
```

---

## 3. Traducción y Herramientas

### 3.1 MDTranslate
```bash
mstbx md-translate --psf sys.psf --coor restart.coor --xsc restart.xsc --toppar-dir ./toppar
```

### 3.2 PDBWriter
```bash
mstbx pdbwriter -i in.pdb -o fixed.pdb --fix --ssbond --ph 7.0
```
*   **Check:** Revisa `pdbwriter_report.log` para ver qué residuos fueron reparados.

---

## 🔍 Lista de Consistencia
1.  **Versión:** `mstbx --version` debe reportar `0.8.0`.
2.  **Autocompletado:** Prueba escribir `mstbx topop[TAB]` para ver si completa `topopsfgen`.
3.  **Logs:** Cada comando debe generar logs claros en la terminal (Colorama habilitado).
