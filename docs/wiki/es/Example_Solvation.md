# 🇪🇸 Ejemplo: Proteína en Solución

Este ejemplo muestra cómo preparar una proteína (ej. Ubiquitina) para simulación en agua con iones.

## 1. Preparación del Sistema (`autopsfgen`)

Utiliza el comando `autopsfgen` con el tipo `sol`:

```bash
mstbx autopsfgen --type sol \
                 --psf step1_pdbreader.psf \
                 --pdb step1_pdbreader.pdb \
                 --salt 0.150 \
                 --ofile ubq_solvated
```

### Parámetros:
*   `--psf / --pdb`: Archivos de estructura y coordenadas iniciales.
*   `--salt`: Concentración de NaCl en mol/L (default 0.150).
*   `--hmr`: (Opcional) Habilita Hydrogen Mass Repartition para pasos de tiempo de 4fs.

## 2. Generación de Configuración NAMD (`namdinputs`)

Una vez construido el sistema (en la carpeta `01build/`), genera los archivos de configuración:

```bash
mstbx namdinputs --type sol \
                 --psf 01build/ubq_solvated.psf \
                 --pdb 01build/ubq_solvated.pdb \
                 --temperature 310 \
                 --mdtime 100
```

### Resultados:
El comando creará las carpetas `02nvt/`, `03npt/` y `04md/` con sus respectivos archivos `.confg` listos para correr en NAMD.

---
[Regresar a la Wiki](Home.md)
