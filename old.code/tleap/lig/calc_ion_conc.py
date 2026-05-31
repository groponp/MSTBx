import math


def calculate_ions(num_water_molecules, protein_charge):

    kcl_molecules_per_liter = 9.03e22  # 150 mM NaCl
    water_molecules_per_liter = 3.33e25  # ~55.3 mol in 1L

    kcl_ratio = kcl_molecules_per_liter / water_molecules_per_liter
    num_kcl_molecules = int(round(kcl_ratio * num_water_molecules))

    # Neutralize the system
    if protein_charge < 0:
        num_cl = num_kcl_molecules
        num_k = num_kcl_molecules - protein_charge # Add extra K+ to neutralize protein charge
    else:
        num_cl = num_kcl_molecules
        num_k = num_kcl_molecules + protein_charge # Add extra K+ to neutralize protein charge


    return num_k, num_cl


if __name__ == "__main__":
    num_water = 29587  # Example from text
    protein_charge = -7  # Example from text

    num_k, num_cl = calculate_ions(num_water, protein_charge)

    print(f"Number of water molecules: {num_water}")
    print(f"Protein charge: {protein_charge}")
    print(f"Number of Na+ ions to add: {num_k}")
    print(f"Number of Cl- ions to add: {num_cl}")