import numpy as np
import src.PCSim.propagation as prop
import src.PCSim.Objects as obj
import src.PCSim.utils as utils
from tqdm import tqdm
import matplotlib.pyplot as plt

    
def Talbot_carpet(n, Source, period, DC, Talbot_multiple, steps, grating_type, pixel_size, design_energy, material = 'Si', grating_height=None):
    """
    Plot Talbot carpet for a grating defined by its period, DC (duty cycle) and grating type: 'custom', 'phase_pi' or 'phase_pi_2'
    """

    if material is None:
        # It is needed a material for initialization
        material = 'Si'

    energies = Source.energies
    mean_energy = Source.mean_energy
    energies_intensities = Source.intensities
    wavelength = 1.23984193/(1000*design_energy) # in um

    Talbot_distance = 2*period**2/(wavelength) *10**(-4) # cm.

    distances = np.linspace(0, Talbot_multiple*Talbot_distance, steps)
    Talbot_carpet = np.zeros((n, steps))

    # Grating definition
    G = obj.Grating(n, period, DC, pixel_size, material, 0,grating_height, grating_type, design_energy = design_energy)
    
    for ie,energy in enumerate(tqdm(energies,  desc='Energy')):
        i = 0
        for distance in distances:
            profile = profile_after_propagation(n, G, energy, pixel_size, distance, PSF_Source=None)
            Talbot_carpet[:,i] += np.transpose(profile) * energies_intensities[ie]
            i+=1

    return Talbot_carpet  
    

def map_Visibility_DC_Energy(n, energies_keV, DC_list, distance_cm, period_um, pixel_size, grating_type='custom', grating_material='Si', design_energy = None,grating_height_um=None,PSF_Source=None):
    energies_array = np.array(energies_keV)
    DC_array = np.array(DC_list)
    V = np.zeros((len(energies_array), len(DC_array)), dtype=float)

    if design_energy is None:
        design_energy = np.mean(energies_array)

    for j, DC in enumerate(tqdm(DC_array, desc='DC list')):

        G = obj.Grating(n, period_um, DC, pixel_size, grating_material, 0,grating_height_um, grating_type, design_energy = design_energy)

        for i, E in enumerate(energies_array):
            profile = profile_after_propagation(
                n, G, E, pixel_size, distance_cm, PSF_Source=PSF_Source)
            V[i, j] = visibility(profile)
    return V, energies_array, DC_array
    

def visibility(profile):
    profile = np.asarray(profile, dtype=np.float64)
    if profile.size == 0:
        return 0.0

    profile = np.nan_to_num(profile, nan=0.0, posinf=0.0, neginf=0.0).ravel()
    max_val = np.max(profile)
    min_val = np.min(profile)
    denom = max_val + min_val

    if np.isclose(denom, 0.0):
        return 0.0

    return float((max_val - min_val) / denom)

def profile_after_propagation(n, G, energy_keV, pixel_size_um, distance_cm, PSF_Source=None):

    trans = G.transmission_function(energy_keV, pixel_size_um)

    u = prop.propagate(trans, pixel_size_um, distance_cm, energy_keV, padding=0)

    I = np.abs(u)**2
    if PSF_Source is not None:
        I = utils.convolve(PSF_Source, I)

    profile = I[n // 2, :].astype(np.float64, copy=False)
    return profile

def plot_visibility_energy_dc(V, energies_keV, DCs, title=None):
    fig, ax = plt.subplots(figsize=(6.5, 5.2), dpi=120)
    im = ax.imshow(V, origin='lower', aspect='auto',extent=[DCs.min(), DCs.max(), energies_keV.min(), energies_keV.max()])
    ax.set_xlabel('Duty cycle (DC)')
    ax.set_ylabel('Energy (keV)')
    if title:
        ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Visibility')
    plt.tight_layout()
    return fig, ax