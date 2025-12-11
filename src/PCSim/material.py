import numpy as np
from pathlib import Path

MATERIALS_DIR = Path(__file__).resolve().parents[2] / "Resources" / "complex_refractive_index"


def list_available_materials(directory):
    directory = MATERIALS_DIR if directory is None else directory
    return [p.stem for p in directory.glob("*.txt")]

def load_material_table(material):
    """
    Load (E_keV, delta, beta) columns for a material.

    Returns:
        E_keV, delta, beta  (all np.ndarray, dtype=float)
    """
    directory = MATERIALS_DIR 
    path = directory / f"{material}.txt"
    if not path.exists():
        raise FileNotFoundError(
            f"Material table not found: {path}\nAvailable: {', '.join(list_available_materials(directory))}"
        )
    try:
        data = np.loadtxt(path, dtype=float, comments="#")
    except Exception as e:
        raise ValueError(f"Failed to load material file '{path}': {e}")

    if data.ndim != 2 or data.shape[1] < 3:
        raise ValueError(f"Material file '{path}' must have at least 3 columns: E_keV, delta, beta.")

    E = data[:, 0].astype(float)
    delta = data[:, 1].astype(float)
    beta = data[:, 2].astype(float)

    return E, delta, beta


def make_material(material, energies_keV, out_of_range = "extrapolate"):
    """
    Interpolate complex refractive index (delta - i*beta) for given energy in keV.
    """

    E_tab, d_tab, b_tab = load_material_table(material) # Info from text files

    E_in = np.asarray(energies_keV, dtype=float)

    E_min, E_max = float(E_tab[0]), float(E_tab[-1])

    if out_of_range == "raise":
        if (E_in < E_min).any() or (E_in > E_max).any():
            raise ValueError(
                f"Energies outside table range [{E_min:.6g}, {E_max:.6g}] keV: {E_in[(E_in<E_min) | (E_in>E_max)]}"
            )
        Eq = E_in
    elif out_of_range == "clip":
        Eq = np.clip(E_in, E_min, E_max)
    elif out_of_range == "extrapolate":
        Eq = E_in

    delta = np.interp(Eq, E_tab, d_tab)
    beta = np.interp(Eq, E_tab, b_tab)

    # Apply ideal material, i.e. Pure Phase or Pure Absorption modes
    if material == "Pure_Phase":
        beta = np.zeros_like(beta)
    elif material == "Pure_Absorption":
        delta = np.zeros_like(delta)
    

    n = delta - 1j * beta 
    
    return n