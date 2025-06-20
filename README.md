<p align="center">
  <img src="logo_adjust.png" width="350" height="250" alt="MSTBx Logo">
</p>

<h1 align="center">MSTBx : Molecular Simulação ToolBox</h1>

<p align="center" style="font-size:1.1em;">
  <b>MSTBx</b> é um pacote <i>in house</i> para preparar e gerar arquivos de configuração para simulações de dinâmica molecular de moléculas em solução ou membrana.<br>
  <b>Compatível com NAMD2 e NAMD3</b>.<br>
  <i>Foco em sistemas grandes, usando PSFGen e VMD.</i>
</p>

---

## ✨ Visão Geral

<p align="justify">
O MSTBx permite preparar sistemas para dinâmica molecular de forma eficiente, especialmente para sistemas grandes (milhões de átomos), aproveitando o poder do PSFGen e VMD. Atualmente, suporta NAMD2 e NAMD3, com planos futuros para GROMACS, AMBER e OpenMM. Métodos como SMD já estão implementados, e ABF, US, GaMD e FEP serão adicionados em breve.<br>
Se tiver dúvidas ou encontrar erros, por favor, abra um <a href="https://github.com/groponp/MSTBx/issues">Issue</a> no GitHub.
</p>

---

## 🚀 Instalação

```bash
git clone git@github.com:groponp/MSTBx.git 
cd MSTBx/ 

# ⚠️ Atenção: Antes de rodar o comando abaixo, troque o prefix para o caminho do seu conda!
# Exemplo: prefix: /home/SEU_USUARIO/miniconda3/envs/mstbx

conda env create -f mstbx.yml
conda activate mstbx

# Adicione o MSTBx ao seu PATH
rota=$(pwd)
echo "export MSTBx=$rota:\$PATH" >> ~/.zshrc   # Para zsh
echo "export MSTBx=$rota:\$PATH" >> ~/.bashrc  # Para bash

# Ative as variáveis de ambiente
source ~/.zshrc   # ou source ~/.bashrc
```

---

## 📚 Exemplos de Uso

### 1️⃣ Ubiquitina em Solução

<details>
<summary><b>Passo a passo</b></summary>

1. Crie uma pasta chamada `ubiquitin` para armazenar os arquivos.
2. Use o <b>PDBReader</b> do CHARMM-GUI para gerar os arquivos PSF/PDB (tutorial <a href="https://www.charmm-gui.org/?doc=demo&id=pdb_reader&lesson=1">aqui</a>).
3. Baixe `step1_pdbreader.pdb` e `step1_pdbreader.psf` e coloque-os na pasta.
4. Monte o sistema e gere os arquivos de configuração para NAMD2/NAMD3.

<p align="justify">
O protocolo padrão inclui: NVT (2 ns, restrição em heavy atoms), NPT (5 ns, mesma restrição) e produção NPT (sem restrições). Ajuste o tempo de simulação conforme necessário.
</p>

```bash
mkdir ubiquitin 
conda activate mstbx
python $MSTBx/GenSol.py --help

# Montar o sistema
python $MSTBx/GenSol.py --psf step1_pdbreader.psf \
                        --pdb step1_pdbreader.pdb \
                        --salt 0.150 \
                        --ofile ubq

# Gerar arquivos de configuração
python $MSTBx/GenMDSolConfg.py --psf 01build/ubq.psf \
                               --pdb 01build/ubq.pdb \
                               --temperature 310 \
                               --mdtime 1
```
</details>

---

### 2️⃣ Proteína-Ligante: Bacterial Aryl Acylamidase + Tilenol

<details>
<summary><b>Passo a passo</b></summary>

1. Gere PSF/PDB e parâmetros do ligante com o PDBReader do CHARMM-GUI (<a href="https://www.charmm-gui.org/?doc=demo&id=protein_ligand&lesson=1">tutorial</a>).
2. Baixe os arquivos e coloque-os na pasta.
3. Monte o sistema e adicione os parâmetros do ligante ao gerar os arquivos de configuração.

```bash
mkdir baat 
conda activate mstbx 
python $MSTBx/GenSol.py --help

# Montar o sistema
python $MSTBx/GenSol.py --psf step1_pdbreader.psf \
                        --pdb step1_pdbreader.pdb \
                        --salt 0.150 \
                        --ofile baat 

# Gerar arquivos de configuração (incluindo parâmetros do ligante)
python $MSTBx/GenMDSolConfg.py --psf 01build/baat.psf \
                               --pdb 01build/baat.pdb \
                               --lparm tyl.prm \
                               --temperature 310 \
                               --mdtime 1  
```
</details>

---

### 3️⃣ Tetramero de Aquaporina em Membrana POPC

<details>
<summary><b>Passo a passo</b></summary>

1. Use o Membrane Builder do CHARMM-GUI (<a href="https://www.charmm-gui.org/?doc=demo&id=membrane_builder&lesson=2">tutorial</a>) para gerar o sistema.
2. Ajuste o tamanho da membrana conforme a extensão da proteína (soma dos valores de X ou Y + 30 Å).
3. Baixe os arquivos `step4_lipid.psf` e `step4_lipid.pdb`.
4. Monte o sistema e gere os arquivos de configuração.

```bash
mkdir aqp 
conda activate mstbx 
python $MSTBx/GenMemb.py --help

# Descompacte e copie os arquivos do CHARMM-GUI
tar -xvzf charmm-gui.tgz
cp charmm-gui-*/step4_lipid.psf  . 
cp charmm-gui-*/step4_lipid.pdb  . 

# Montar o sistema
python $MSTBx/GenMemb.py --psf step4_lipid.psf \
                         --pdb step4_lipid.pdb \
                         --salt 0.150 \
                         --ofile aqp

# Gerar arquivos de configuração
python $MSTBx/GenMDMembConfg.py --psf 01build/aqp.psf \
                                --pdb 01build/aqp.pdb \
                                --temperature 310 \
                                --mdtime 1
```
<p align="justify">
<b>Nota:</b> O MSTBx é muito mais eficiente que o CHARMM-GUI para sistemas grandes. Por exemplo, sistemas como a proteína spike do SARS-CoV-2 podem ser preparados em ~30 min, enquanto no CHARMM-GUI podem levar até 8 horas.
</p>
</details>

---

## 👨‍💻 Autor

<p align="center">
<b>Ropón-Palacios G.</b><br>
Departamento de Física,<br>
Instituto de Biociências, Letras e Ciências Exatas - IBILCE,<br>
Universidade Estadual Paulista "Júlio de Mesquita Filho" - UNESP<br>
Rua Cristóvão Colombo, 2265 - Jardim Nazareth<br>
São José do Rio Preto/SP - CEP 15054-000<br>
E-mail: <a href="mailto:georcki.ropon@unesp.br">georcki.ropon@unesp.br</a>
</p>

---

## 📄 Licença

<p align="center">
  <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GPLv3</a>
</p>
