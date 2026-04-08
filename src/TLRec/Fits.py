import numpy as np
from scipy import optimize, fftpack
import src.TLRec.utils as utils
import src.TLRec.Correction as Correction

try:
    from numba import njit
except Exception as err:
    #print(f'Numba cannot be imported: {err}')
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

"""
In this python file are located different functions to make the fit of the data points to a sine/cosine function.
Some algorithms use the FFT and others use a least squares method.

Author: Víctor Sánchez Lara
Date: April 2022
"""

#@jit(nopython=True, parallel=False, cache=True)
def fastest_fit_fft(images):
  """
  Fast Fourier Transform based algorithm to retrieve the Sine's like Modulation Curve. It does the 
  FFT to the image along the phase step axis (axis=0) and then it calculates the phase as the angle of the first
  peak of the FFT image. The amplitude is calculated by the intensity of the first frequency peak and the offset
  with mean value of each pixel along the phase step axis. You can check Reference [1] to see more information and
  an aplication.
  
  Reference [1]: Hashimoto K, Takano H, Momose A. Improved reconstruction method for phase stepping 
                data with stepping errors and dose fluctuations. Opt Express. 
                2020 May 25;28(11):16363-16384. doi: 10.1364/OE.385236. PMID: 32549461.

  Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector. The shape should be
      (N, Y, X) where N is the number of phase steps, Y is the number of pixels in the vertical orientation and X 
      the number of pixels in the horizontal orientation.

  Returns:
      offset (numpy array): Offset of the Modulation Curve of all pixels
      phase (numpy array): Phase of the Modulation Curve of all pixels
      visibility (numpy array): Visibility of the Modulation Curve of all pixels
      
  """
  (z,y,x) = images.shape
  spectrum = fftpack.fft(images, axis=0)/z
  p = np.angle(spectrum[1,:,:])
  amplitude = np.abs(spectrum[1,:,:]*2)
  offset = np.sum(images, axis=0)/z
  visibility = amplitude/offset
  return offset, p, visibility


def fast_fit_fft(images):
  """
   Fast Fourier Transform based algorithm to retrieve the Sine's like Modulation Curve. It does the 
  FFT to the image along the phase step axis (axis=0) and get the first two components of the FFT 
  (frequency = 0 and the most intense frequency). Then, it gets the components of the FFT pixel-wise 
  and make the calculations to obtain the offset, phase and visibility images. 

  Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector. The shape should be
      (N, Y, X) where N is the number of phase steps, Y is the number of pixels in the vertical orientation and X 
      the number of pixels in the horizontal orientation.

  Returns:
      offset (numpy array): Offset of the Modulation Curve of all pixels
      phase (numpy array): Phase of the Modulation Curve of all pixels
      visibility (numpy array): Visibility of the Modulation Curve of all pixels
  """
  (z,y,x) = images.shape
  steps = np.arange(0,images.shape[0],1)*2*np.pi/images.shape[0]
  Matrix = np.ones((z,2), dtype=complex)
  Matrix[:,1] = np.exp(1j*steps)
  A = np.linalg.pinv(Matrix)
  images_flat = images.reshape(z, -1)
  coeffs = A @ images_flat
  c0 = coeffs[0, :].real.reshape(y, x)
  c1 = coeffs[1, :].reshape(y, x)

  offset = c0
  p = np.arctan2(c1.imag,c1.real)
  visibility = np.sqrt(c1.imag**2+c1.real**2)/c0
  return offset, p, visibility

def fit_fft(images):
    """
  This algorithm, based on the Fast Fourier Transform, is designed to retrieve a sine-like modulation curve. 
  Its distinguishing feature from the previously defined function is that it specifically searches for the peak 
  of the first harmonic

  Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector. The shape should be
      (N, Y, X) where N is the number of phase steps, Y is the number of pixels in the vertical orientation and X 
      the number of pixels in the horizontal orientation.

  Returns:
      offset (numpy array): Offset of the Modulation Curve of all pixels
      phase (numpy array): Phase of the Modulation Curve of all pixels
      visibility (numpy array): Visibility of the Modulation Curve of all pixels
      
    """
    (z,y,x) = images.shape
    module = np.zeros((y,x))
    phase = np.zeros((y,x))

    spectrum = fftpack.fft(images, axis=0)/z
    offset = np.amax(spectrum, axis=0).real
    peaks = np.argmax(np.abs(spectrum[1:, :, :]), axis=0) + 1
    ii = np.arange(y)[:, None]
    jj = np.arange(x)[None, :]
    selected = spectrum[peaks, ii, jj]
    a = 2 * selected.real
    b = 2 * selected.imag

    phase = np.arctan(b / a)
    phase[(a < 0) & (b > 0)] -= np.pi
    phase[(a < 0) & (b < 0)] += np.pi
    module = np.sqrt(np.power(a, 2) + np.power(b, 2))

    for i in range(y):
      for j in range(x):
        if offset[i, j] == 0 or module[i, j] == 0:
          offset[i, j] = offset[i, j-1]
          phase[i, j] = phase[i, j-1]
          module[i, j] = module[i, j-1]
    visibility = utils.calculate_visibility(module,offset)
    return offset,  phase, visibility    
   


def fit_least_square(images):
    """
    Least-squares based algorithm to fit a cosine model for each pixel modulation curve.
    For every pixel, the method estimates amplitude, angular frequency, phase, and offset
    using non-linear optimization (`scipy.optimize.curve_fit`). Then, it derives the
    visibility as amplitude divided by offset.

    Args:
        images (numpy array): 3 dimensional array with the raw images recorded by the detector.
            The shape should be (N, Y, X) where N is the number of phase steps, Y is the number
            of pixels in the vertical orientation and X the number of pixels in the horizontal
            orientation.

    Returns:
        Offset (numpy array): Offset of the Modulation Curve of all pixels.
        Phase (numpy array): Phase of the Modulation Curve of all pixels.
        Visibility (numpy array): Visibility of the Modulation Curve of all pixels.
        frequency (numpy array): Estimated angular frequency of the fit for all pixels.
    """

    (z,y,x) = images.shape
    step = 1
    tt = np.arange(0,z,step)
    Offset = np.zeros((y,x))
    Phase = np.zeros((y,x))
    Visibility =np.zeros((y,x))
    guess_freq = 1/(2*np.pi)
    frequency = np.zeros((y,x))
    for ii in range(y):
      for jj in range(x):
        yy = images[:,ii,jj]
        guess_freq = utils.calculate_guess_freq(tt, yy)
        guess_amp, guess_offset = utils.calculate_guess_amp_offset(yy)
        guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])
        try:
          popt, pcov = optimize.curve_fit(utils.cosfunc, tt, yy, p0=guess)
        except:
          A = 0
          w = 0
          p = 0
          c = guess_offset
          popt = [A, w, p, c]

        A, w, p, c = popt
        if A == 0:
          A = Visibility[ii,jj-1]*Offset[ii,jj-1]
          p = Phase[ii,jj-1]
          c = Offset[ii,jj-1]
          w = frequency[ii,jj-1]
        if c == 0:
          A = Visibility[ii,jj-1]*Offset[ii,jj-1]
          p = Phase[ii,jj-1]
          c = Offset[ii,jj-1]
          w = frequency[ii,jj-1]
  
        A, p = utils.check_amp_phase(A, p)
        Offset[ii,jj] = c
        Phase[ii,jj] = p
        Visibility[ii,jj] = A/c
        frequency[ii,jj] = w
        
    return Offset, Phase, Visibility, frequency
  
@njit(parallel=False, cache=True, fastmath=False)
def opt_fit_least_square(images,A):
    """
    Optimized pixel-wise least-squares solver using a precomputed design matrix.
    It solves the linear system for the model parameters (offset, cosine term,
    and sine term) for each detector pixel.

    Args:
        images (numpy array): 3 dimensional array with the raw images recorded by the detector.
            The shape should be (N, Y, X).
        A (numpy array): Design matrix with shape (N, 3) used in the linear least-squares fit.

    Returns:
        o (numpy array): Offset term for all pixels.
        a (numpy array): Cosine coefficient for all pixels.
        b (numpy array): Sine coefficient for all pixels.
    """
    A = np.asarray(A, dtype = np.float64)
    (z,y,x) = images.shape
    # It may be more efficient
    C = np.linalg.inv(A.T @ A) @ A.T
    images_flat = images.reshape(z, y * x)
    coeffs = C @ images_flat
    o = coeffs[0, :].reshape(y, x)
    a = coeffs[1, :].reshape(y, x)
    b = coeffs[2, :].reshape(y, x)     
    return o, a, b

  
def Step_correction(images):
    """
    Corrects phase-step errors by minimizing a function.
    The function estimates step deviations, builds an updated
    design matrix and solves for pixel-wise model coefficients.

    Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector.
        The shape should be (N, Y, X).

    Returns:
      o (numpy array): Offset term for all pixels.
      a (numpy array): Cosine coefficient for all pixels.
      b (numpy array): Sine coefficient for all pixels.
      new_steps (numpy array): Corrected phase-step positions.
    """
    steps = np.arange(0,images.shape[0],1)*2*np.pi/images.shape[0]
    error = np.zeros((images.shape[0]))
    new_errors = optimize.minimize(Correction.Improve_reconstruction_minimization_steps, error, Correction.calculate_C_matrix(images))
    new_errors = new_errors.x
    print(new_errors)
    step_errors = new_errors[0:images.shape[0]]
    A = np.ones((images.shape[0], 3))
    new_steps = steps+step_errors
    A[:,1] = np.cos(new_steps)
    A[:,2] = np.sin(new_steps)
    #o, a, b =opt_fit_least_square(images, A)
    o, a, b =resolve_eq(images, A)
    return o, a, b, new_steps
  
@njit(parallel=False, cache=False, fastmath=True)  
def resolve_eq(images,A ):
  """
  Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector.
          The shape should be (N, Y, X).
      A (numpy array): Design matrix with shape (N, 3).

  Returns:
      o (numpy array): Offset term for all pixels.
      a (numpy array): Cosine coefficient for all pixels.
      b (numpy array): Sine coefficient for all pixels.
  """
  (z,y,x) = images.shape
  # It may be more efficient
  C = np.linalg.inv(A.T@A) @ A.T
  images_flat = images.reshape(z, y * x)
  coeffs = C @ images_flat
  o = coeffs[0, :].reshape(y, x)
  a = coeffs[1, :].reshape(y, x)
  b = coeffs[2, :].reshape(y, x)
  return o, a, b