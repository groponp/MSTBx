# MSTBx : Molecular Simulação ToolBox 
<div style="display: flex;">
  <img src="logo_adjust.png" width="350" height="250" style="flex: 1;"> 
  <div style="margin-left: 20px;">
    <p style="text-align: justify;">
      Este repositorio contém o MSTBx, um código in house que permite preparar e gerar arquivos de configuração para realizar simulações de dinâmica molecular de moléculas em solução ou em membrana. No momento, esta ferramenta só gera sistemas compatíveis com NAMD2 ou NAMD3, mas no futuro, facilitará a interpolação dos sistemas para GROMACS, AMBER e openMM. Atualmente, a Dinâmica Molecular Guiada (Steered Molecular Dynamics -SMD) está implementada. Em breve, os métodos de ABF, US, GaMD e FEP serão adicionados. A principal diferença de nosso código para aqueles que existem ja, é que faz uso das capacidades de PSFGen e VMD para generar "Big Systems", de milhões de átomos. Se você tiver alguma dúvida ou erro para relatar, por favor, abra um <a href="https://github.com/groponp/MSTBx/issues">Issue</a>.
    </p>
  </div>
</div>

### Instalação

```bash
git clone git@github.com:groponp/MSTBx.git 
cd MSTBx/ 
conda env create -f mstbx.yml
conda activate mstbx
rota=$(pwd)            #! Obtenha a rota completa, copy o ob
echo "export MSTBx=/$rota:$PAHT" >> ~/.zshrc # se tem zsh shell
echo "export MSTBx=/$rota:$PAHT" >> ~/.bashrc # se tem bash shell


```

### Exemplos 
<p style="text-align: justify;">
Nesta secção podemos encontrar algums exemplos de uso da ferramenta. Lembre que estes são só exemplos, e eles podem ser diferentes a suas encesidades, então, se você quer mais detalhe da ferramenta, sempre use --help. Nota: Estes exemplos asumen que você coneche o tem idea de como usar charmm-gui, se não for assim, revise os video demos, que eles tem na sua <a href="https://www.charmm-gui.org/?doc=demo">página</a>. 
</p>

#### 1) Ubiquitina em Solução 
<p style="text-align: justify;">
1) Crie uma pasta de nome ubiquitin, onde tuda informação será armazenada. Seguido faremos uso da ferramenta PDBReader do charmm-gui, para generar o PSF/PDB. Para saber como fazer isso olhe o tutorial <a href="https://www.charmm-gui.org/?doc=demo&id=pdb_reader&lesson=1">here</a>. 2) Use o pdb id 1UBQ em PDBReader e descarregue o PDB/PSF (step1_pdbreader.pdb/step1_pdbreader.psf) generado pelo PDBReader e salve na sua pasta ubiquitin. 3) Agora faremos uso do arquivos de coordenadas (PDB) e topología (PSF), para generar nosso sistema. 4) Finalmente, vamos gerar os arquivos de configuração para rodar a simulação com NAMD2 ou NAMD3. Netes ponto final, você esta pronto para realizar sua simulação. È recomendado revisar todos os arquivos para conferir que tudo foi feito corretamente. O protocolo da simulação implementado ensta ferramenta consiste nos siguentes pasos: NVT 2 ns com restrição do heavy atoms, NPT 5 ns mantendo a mesma restrição e NPT produção sem nenhuma restrição. Na produção, você pode escolher o tempo da simulação, no caso de este exemplo usamo só 1 ns.  
</p>

```bash
mkdir ubiquitin 
conda activate mstbx            # Ativa o env de conda. 
python $MSTBx/GenSol.py --help  # Mostra a informação da ferramenta.

#! Ensamblar o sistema. 
python $MSTBx/GenSol.py --psf step1_pdbreader.psf \  # PSF é a topología.
--pdb step1_pdbreader.pdb \                          # PDB são as coordenadas.
--salt 0.150 \                                       # A concentração de sal a usar. so suporta NaCl.
--ofile ubq                                          # Nome do output. 

#! Gerar os arquivos de configuração.
#! Nota no paso anterior se genera automaticamente uma pasta de nome 01build,
#! onde conten tuda a informação, so sistema. Pode dar uma olhada para mais detalhe. 
python $MSTBx/GenMDSolConfg.py --psf 01build/ubq.psf \  # PSF generado no paso anterior.
--pdb 01build/ubq.pdb \                                 # PDB generado no paso anterior.
--temperature 310 \                                     # Temperature em Kelvin. 
--mdtime 1                                              # Tempo de simulação em nanosegundos. 
```

#### 2) Bacterial Aryl Acylamidase em complexo com Tilenol (small molecule)
<p style="text-align: justify;">
Neste exemplo, vamos mostar como ensamblar o sistema proteína-ligante. 1) Generamos os arquivos PSF/PDB, e os parametros (aquivo *.prm or *.str) do ligante, com PBDReader, para esto pode olhar o tutorial de charmm-gui <a href="https://www.charmm-gui.org/?doc=demo&id=protein_ligand&lesson=1">here</a>. Use o pdb id 4YJI, para este exemplo, cá selecione o ligante 	TYL, e a proteína só. 2) Descarregue o PSF/PDB e os archivos *.rtf e *.prm do ligante, estos arquivos contem a informação da topología e os parametros que se precisam para realizar a simulação, se você ainda nao tem muito conhecimento da estrutura de estos arquivos, de uma olhada neste <a href="https://www.charmm-gui.org/?doc=lecture&module=molecules_and_topology&lesson=3">lecture</a> de charmm-gui. 3) Use GenSol.py para ensamblar o sistema. 4) Finalmente, generamos os arquivos de configuração, cá precisamos adicionar um comando "--lparm", para adicionar os parametros do ligante. O protocolo da simulação cá, é o mesmo do exemplo 1. 

</p>

```bash 
mkdir baat 
conda activate mstbx 
python $MSTBx/Gensol.py --help    # Obtenha mais informação. 
#! Ensamblar o sistema. 
python $MSTBx/GenSol.py --psf step1_pdbreader.psf \
--pdb step1_pdbreader.pdb \
--salt 0.150 \
--ofile baat 

#! Gerar os aquivos de configuração. 
python $MSTBx/GenMDSolConfg.py --psf 01build/baat.psf \
--pdb 01build/baat.pdb \
--lparm tyl.prm \               # parametro do ligante.
--temperature 310 \
--mdtime 1  
```

#### 3) Tetramero de Aquaporina em membrana de 1-palmitoyl-2-oleoyl-glycero-3-phosphocholine (POPC)
<p style="text-align: justify;">
Neste exemplo vamos mostrar como ensamblar o sistema de o tetrámero de aquaporina em membrana constituída do fosfolipídeo POPC.  1) Para isto, vamos usar a ferramenta Membrane Builder de charmm-gui, para olhar os detalhes desta ferramenta olhe <a href="https://www.charmm-gui.org/?doc=demo&id=membrane_builder&lesson=2">here</a>. Use o pdb id 3C02, 2) Cá neste ponto, tem alguns detalhes: a) Ao momento se criar o sistema selecione "membrane bilayer", e deixe em "Download Source" a opção OPM, e só seleccione a proteina. b) No STEP 1 (orientação), seleccione "Use PDB Orientation", d) No STEP 2 nós podemos observar isto: 

Protein Top Area: 4054.2678\
Protein Bot Area: 4026.77424\
X Extent: -41 to 41\
Y Extent: -41 to 41\
Z Extent: -25 to 28

Neste caso, esta informação pode nós fornecer una idea, de como escolher o tamanho da membrana no plano xy. Como regra de thumb, escolhemos o valor de X ou Y mais longo, neste caso é o a soma dos valores (min e max) do x ou y, tem o mesmo valor, que é 82 Angstroms. Por tanto podemos escolher qualquer um. Embora, em outro casos, e sempre melhor escolher o valor mais longo, i.e se eu tenho valores de 82 e 90, então usar 90. Agora a este valor, adicionamos 30 Angstrom adicionais, que agregam 15 Angstroms adicionais a cada lado no plato XY. Esse valor é seleccionado para evitar que ás moléculas interagem com elas mesmas.  Então o valor do plano XY final é 112 Angstroms, e) Seleccione o fofolipídeo POPC, com valores 1 e 1 para upper e lower monocapa. (Para mais detalhe revise <a href="https://www.charmm-gui.org/?doc=demo&id=membrane_builder&lesson=2">here</a>). Finalmente, avance até o STEP 4, deixando todos os valores por default e descarregue o PSF/PDB. 

Alter: Charmm-gui pode fazer todos estos pasos, mas a diferença é que a medida que o tamanho do sistema crece, charmm-gui toma mais tempo, para solvatar e adicionar os iones, o que não e eficiente, se quiser preparar multiples sistemas, por exemplo, para preparar todo o sistema da proteína spyke de sars-cov-2 este poderia tomar 8 hrs de tempo, com nossa ferramenta, ele toma so 30 min. 

</p>

```bash
mkdir aqp 
conda activate mstbx 
python $MSTBx/GenMemb.py --help    # Obtenha mais informação

#! Desempacote o charmm-gui.tgz
tar -xvzf charmm-gui.tgz
cp charmm-gui-*/step4_lipid.psf  . 
cp charmm-gui-*/step4_lipid.pdb  . 

#! Ensamblar o sistema.
#! Os comandos são similares para GenSol.py.
python $MSTBx/GenMemb.py --psf step4_lipid.psf \
--pdb step4_lipid.pdb \
--salt 0.150 \
--ofile aqp

#! Gerar os aquivos de configuração. 
python $MSTBx/GenMDMembConfg.py --psf 01build/aqp.psf \
--pdb 01build/aqp.pdb \
--temperature 310 \
--mdtime 1
```

## Authors 
Main Developer: 

**Ropón-Palacios G.**  
Departamento de Física,   
Instituto de Biociências, Letras e Ciências Exatas - IBILCE,   
Universidade Estadual Paulista "Júlio de Mesquita Filho" - UNESP,   
Rua Cristóvão Colombo, 2265 - Jardim Nazareth - São José do Rio Preto/SP - CEP 15054-000  
E-mail: georcki.ropon@unesp.br

## License
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)