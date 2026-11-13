import numpy as np
from functools import lru_cache

_FREQ_GRID_CACHE_SIZE = 8
_PROPAGATOR_CACHE_SIZE = 16


@lru_cache(maxsize=_FREQ_GRID_CACHE_SIZE)
def _frequency_grid(shape, pixel_size):
    """Cache the spatial-frequency grid for a given array shape and pixel size."""
    H, W = int(shape[0]), int(shape[1])
    fs = 1.0 / float(pixel_size)
    fx = np.linspace(-fs / 2.0, fs / 2.0 - fs / W, W, dtype=np.float64)
    fy = np.linspace(-fs / 2.0, fs / 2.0 - fs / H, H, dtype=np.float64)
    FX, FY = np.meshgrid(fx, fy, indexing='xy')
    return FX.astype(np.float64, copy=False), FY.astype(np.float64, copy=False)


@lru_cache(maxsize=_PROPAGATOR_CACHE_SIZE)
def create_propagator(shape, pixel_size, distance, energy):
    """Create a Fresnel propagator, cached per shape/energy/distance."""
    # Fresnel propagator
    # Energy is in keV and distance in cm
    wavelength = 1.23984193 / (1000 * float(energy))  # in um
    DOD = float(distance) * 10**4  # convert into um
    FX, FY = _frequency_grid(shape, pixel_size)
    propagator = np.exp(-1j * np.pi * wavelength * DOD * (FX**2 + FY**2))
    return propagator.astype(np.complex64, copy=False)


def clear_propagator_cache():
    """Free the memory held by the propagator/frequency-grid caches.

    Call this between independent simulation runs (e.g. at the start of
    Experiment_Inline / Experiment_Phase_Stepping) so that distance/energy
    combinations from a previous run don't keep large arrays alive in
    memory for the rest of the Python session.
    """
    create_propagator.cache_clear()
    _frequency_grid.cache_clear()


def propagate(Wavefront, pixel_size, distance, energy, padding=0):
    """To avoid artifacts padding is applied"""
    if pixel_size <= 0:
        raise ValueError("pixel_size must be > 0.")
    if energy <= 0:
        raise ValueError("energy must be > 0.")
    if padding < 0:
        raise ValueError("padding must be >= 0.")

    H0, W0 = Wavefront.shape
    pad_pixels = padding

    W = Wavefront
    if pad_pixels > 0:
        Wavefront_padded = padding_wavefront(pad_pixels, W)
    else:
        Wavefront_padded = W

    n = Wavefront_padded.shape

    # Evaluate distance
    zmax = zmax_fresnel(n[0], pixel_size, energy)
    num_prop = number_propagations(distance, zmax)
    sub_distance = distance / num_prop

    U = np.fft.fftshift(np.fft.fft2(Wavefront_padded))
    H = create_propagator(tuple(n), pixel_size, sub_distance, energy)

    for _ in range(num_prop):
        U = H * U

    u = np.fft.ifft2(np.fft.ifftshift(U))  # Propagated Wavefront
    if pad_pixels > 0:
        u = u[pad_pixels:-pad_pixels, pad_pixels:-pad_pixels]

    return u

def padding_wavefront(pad_pixels, U):
    u = np.pad(U, ((pad_pixels, pad_pixels), (pad_pixels, pad_pixels)), mode='edge')
    return u


def zmax_fresnel(N, pixel_size, energy):
    if pixel_size <= 0:
        raise ValueError("pixel_size must be > 0.")
    if energy <= 0:
        raise ValueError("energy must be > 0.")

    wavelength = 1.23984193/(1000*energy) # in um
    zmax = (N * pixel_size * pixel_size) / wavelength
    return zmax * 10**(-4) # convert into cm

def number_propagations(z, zmax):
    if z <= zmax:
        return 1
    return int(np.ceil(z /zmax))