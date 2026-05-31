# MSTBx Testing Manual & Debugging Guide

Manual actualizado para la arquitectura modular v0.7.6.

---

## 🛠️ Módulo: autopsfgen
**Objetivo:** Construir sistemas con control granular de padding.

```bash
mstbx autopsfgen --type sol --psf protein.psf --pdb protein.pdb --padding 18
```

---

## ⚙️ Módulo: md-inputs
**Objetivo:** Generar archivos para dinámica estándar.

```bash
# NAMD Solución
mstbx md-inputs --engine namd --type sol --psf 01build/sys.psf --pdb 01build/sys.pdb --dcdfreq 10.0
```

---

## ⚙️ Módulo: smd-inputs
**Objetivo:** Generar archivos para Steered MD.

```bash
mstbx smd-inputs --engine namd --psf 01build/sys.psf --pdb 01build/sys.pdb \
                 --selpull "segid PROA and resid 100" \
                 --selanchor "segid PROA and resid 1" \
                 --target-center 50
```

---

## ⚙️ Módulo: metad-inputs
**Objetivo:** Generar archivos para Metadinámica.

```bash
mstbx metad-inputs --engine namd --psf 01build/sys.psf --pdb 01build/sys.pdb \
                   --sel1 "segid PROA" --sel2 "segid PROB" \
                   --target-distance 60
```

---

## 🧪 Otros Módulos
*   **pdbwriter**: `mstbx pdbwriter -i in.pdb -o out.pdb --fix`
*   **colabfold**: `mstbx colabfold -i ./fastas -o ./results`
*   **mkdocking-cmplx**: `mstbx mkdocking-cmplx -p prot.pdb -d dock.pdbqt -o complex.pdb`
