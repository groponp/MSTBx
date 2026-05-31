#!/bin/bash
#! Este script, revisa se os metodos que de obabel são dão
#! o mesmo resultado ao momento de adicionar cargas.
#! link para o primeiro método: https://wiki.docking.org/index.php/Minimize_protein-ligand_complex_with_AMBER

ligand="sustiva.pdb"

#! metodo 1 ao adicionar o -p a difenças entre atomso da 0.
#! mas no metodo original eles não usam esse flag.
obabel -ipdb $ligand -omol2 -O metodo1.mol2 -charge # -p 7.4
#! metodo 2  implementado em mstbx
obabel -ipdb sustiva.pdb -omol2 -O metodo2.mol2 --partialcharge gasteiger -p 7.4 --log-level 2 -d

for mol2 in metodo1.mol2 metodo2.mol2; do
    charge=$(awk 'NF==9 {sum+=$9} END {printf "%.4f", sum}' $mol2)
    echo "$mol2: carga total = $charge"
done

#! fazer uma comparação átomo para átomo em ambos os metodos
#! ainda que tem difenças em alguns deles (quando -p não é usando no
#! no método 1), #! apos usar antechamber ele ira a corrigir as cargas parciais
paste <(awk 'NF==9 {print $1, $9}' metodo1.mol2) \
      <(awk 'NF==9 {print $9}' metodo2.mol2) | \
      awk '{printf "%-6s  m1=%.4f  m2=%.4f  diff=%.4f\n", $1, $2, $3, $2-$3}'
