"""Array backend selection (NumPy/CuPy) for the TLRec reconstruction algorithms.

CuPy is an optional dependency. If it is not installed, or no CUDA device is
found, everything falls back transparently to NumPy.

Author: Víctor Sánchez Lara
"""
import numpy as np

try:
    import cupy as cp
    _CUPY_IMPORTED = True
except Exception:
    cp = None
    _CUPY_IMPORTED = False

_gpu_available_cache = None


def gpu_available():
    """Return True if CuPy is installed and a working CUDA device is found. Result is cached."""
    global _gpu_available_cache
    if _gpu_available_cache is None:
        _gpu_available_cache = False
        if _CUPY_IMPORTED:
            try:
                _gpu_available_cache = cp.cuda.runtime.getDeviceCount() > 0
            except Exception:
                _gpu_available_cache = False
    return _gpu_available_cache


def get_xp(use_gpu=False):
    """Return the array module to use: cupy if requested/available, numpy otherwise."""
    if use_gpu and gpu_available():
        return cp
    return np


def is_gpu_array(array):
    """Return True if array is a CuPy (device) array."""
    return _CUPY_IMPORTED and isinstance(array, cp.ndarray)


def asnumpy(array):
    """Bring an array back to host memory regardless of its backend."""
    if is_gpu_array(array):
        return cp.asnumpy(array)
    return np.asarray(array)


def warmup(xp):
    """Trigger CuPy's first-call kernel compilation ahead of time on a tiny array."""
    if xp is not np:
        a = xp.ones((8, 8), dtype=xp.float64)
        _ = a @ a
        xp.cuda.Stream.null.synchronize()
