<p align="center">
  <img src="logo_adjust.png" width="350" height="250" alt="MSTBx Logo">
</p>

<h1 align="center">MSTBx: Molecular Simulation ToolBox (v0.8.9-beta)</h1>

<p align="center">
  <b>A modular Python ecosystem to streamline Molecular Dynamics preparation, configuration, and translation.</b>
</p>

<p align="center">
  <a href="#en">🇺🇸 English</a> | 
  <a href="#pt-br">🇧🇷 Português</a> | 
  <a href="#es">🇪🇸 Español</a>
</p>

---

<h2 id="en">🇺🇸 English</h2>

### ✨ Overview
**MSTBx** is a modular CLI-based suite designed to automate the heavy lifting of MD simulations. It leverages **VMD**, **PSFGen**, and **MDAnalysis** to handle systems ranging from small ligands to massive complexes with millions of atoms.

*   **Primary Engine:** NAMD2/3.
*   **Secondary Support:** GROMACS, AMBER, OpenMM.
*   **Efficiency:** Up to **16x faster** than web-based builders for large systems (e.g., SARS-CoV-2 Spike).

### 🚀 Installation & Setup

<details open>
<summary><b>View Installation Steps</b></summary>

#### 1. Environment Setup (Conda)
```bash
# Create and activate a dedicated environment
conda create -n mstbx python=3.12
conda activate mstbx

# Clone the repository
git clone git@github.com:groponp/MSTBx.git
cd MSTBx

# Install in development mode
pip install -e .
```

#### 2. Persistent Shell Completion (Zsh)
To enable TAB completion without activating the environment every time, add this to your `~/.zshrc`:
```bash
# MSTBx TAB Completion
eval "$(_MSTBX_COMPLETE=zsh_source $HOME/miniconda3/envs/mstbx/bin/mstbx)"
```
</details>

### 🛠 Command Reference & Examples

<details>
<summary><b>1. topopsfgen: System Building (Solvation/Membrane)</b></summary>

Builds systems with water, ions, or lipid bilayers.

*   **Ubiquitin in Solution:**
    ```bash
    # Cubic box, 18A padding, 0.15M NaCl
    mstbx topopsfgen --env solution --psf protein.psf --pdb protein.pdb --salt 0.150 --padding 18.0 --ofile ubq
    ```
*   **Aquaporin in Membrane:**
    ```bash
    # Automatic Z-padding (25A), square XY box
    mstbx topopsfgen --env membrane --psf step4_lipid.psf --pdb step4_lipid.pdb --salt 0.150 --ofile aqp
    ```
</details>

<details>
<summary><b>2. md-inputs: Protocol Generation</b></summary>

Generates Minimization, NVT, NPT, and Production scripts.

*   **Protein-Ligand NAMD Production:**
    ```bash
    # 200ns at 310K, saving every 50ps, with ligand parameters
    mstbx md-inputs --engine namd --env solution --psf ionized.psf --pdb ionized.pdb \
                    --temperature 310 --mdtime 200 --dcdfreq 50.0 --lparm ligand.str
    ```
</details>

<details>
<summary><b>3. Advanced Sampling (SMD & Metadynamics)</b></summary>

*   **Steered Molecular Dynamics (SMD):**
    ```bash
    # Pulling a ligand from a site at 5A/ns
    mstbx smd-inputs --psf system.psf --pdb system.pdb --selpull "resname LIG" \
                     --selanchor "protein and backbone" --target-center 45.0 --velocity 5.0
    ```
*   **Well-Tempered Metadynamics:**
    ```bash
    # Distance-based sampling between two domains
    mstbx metad-inputs --psf complex.psf --pdb complex.pdb --sel1 "segid PROA" \
                       --sel2 "segid PROB" --target-distance 30.0 --hill 0.2
    ```
</details>

---

<h2 id="pt-br">🇧🇷 Português</h2>

### ✨ Visão Geral
O **MSTBx** é um pacote modular para automatizar a preparação de simulações de Dinâmica Molecular. Focado em **sistemas grandes** (milhões de átomos), ele utiliza PSFGen e VMD para entregar resultados muito mais rápidos que ferramentas web.

*   **Foco Principal:** NAMD2 e NAMD3.
*   **Performance:** Prepare sistemas como a Spike do SARS-CoV-2 em ~30 min (contra 8h em ferramentas convencionais).

### 📚 Exemplos de Uso Detalhados

<details>
<summary><b>Proteína-Ligante em Solução</b></summary>

1. Gere os arquivos PSF/PDB iniciais (ex: via CHARMM-GUI PDBReader).
2. Monte o sistema e gere os inputs com parâmetros do ligante.

```bash
# 1. Montar o sistema (Solvatação e Ionização)
mstbx topopsfgen --env solution --psf protein_ligand.psf --pdb protein_ligand.pdb --salt 0.150 --ofile complex

# 2. Gerar protocolos (NAMD, 310K, 100ns)
mstbx md-inputs --engine namd --env solution --psf 01build/complex.psf --pdb 01build/complex.pdb \
                --lparm ligand.prm --temperature 310 --mdtime 100
```
</details>

---

<h2 id="es">🇪🇸 Español</h2>

### ✨ Visión General
**MSTBx** permite preparar sistemas para dinámica molecular de forma eficiente. Aprovecha el poder de PSFGen y VMD para sistemas complejos (proteína-ligando, membranas, etc.).

### 🛠 Referencia de Comandos

<details>
<summary><b>pdbwriter: Preparación Avanzada de PDB</b></summary>

Repara huecos, protona y detecta puentes disulfuro.

```bash
# Reparar átomos faltantes, protonar a pH 7.4 y añadir SSBONDs
mstbx pdbwriter -i original.pdb -o fixed.pdb --fix --ph 7.4 --ssbond
```
</details>

---

### 👨‍💻 Author | Autor
**Ropón-Palacios G.**  
*UNESP - São José do Rio Preto/SP*  
📧 [georcki.ropon@unesp.br](mailto:georcki.ropon@unesp.br)

### 📄 License | Licença
Licensed under the **MIT License**. (GPLv3 in previous versions).
