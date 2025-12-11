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
  c0 = np.zeros((y,x), dtype=float)
  c1 = np.zeros((y,x), dtype=complex)
  for ii in range(y):
    for jj in range(x):
      c0[ii,jj], c1[ii,jj] = np.matmul(A,images[:,ii,jj].T)

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
    offset = np.zeros((y,x))   
    module = np.zeros((y,x))
    phase = np.zeros((y,x))

    spectrum = fftpack.fft(images, axis=0)/z
    offset = np.amax(spectrum, axis=0).real
    #phase, module = np.apply_along_axis(utils.alongaxis_calculate_sine_parameters(spectrum), axis=0)
     #For each pixel of the images we do the fft along the z axis, to obtain the parameters of the Modulation Curve
    for ii in range(y):
      for jj in range(x):
        phase[ii,jj], module[ii,jj] = utils.calculate_sine_parameters(spectrum[:,ii,jj])
        if offset[ii,jj] == 0 or module[ii,jj] == 0:
          offset[ii,jj] = offset[ii,jj-1]
          phase[ii,jj] = phase[ii,jj-1]
          module[ii,jj] = module[ii,jj-1]    
    visibility = utils.calculate_visibility(module,offset)
    return offset,  phase, visibility    
   


def fit_least_square(images):
    
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
    A = np.asarray(A, dtype = np.float64)
    (z,y,x) = images.shape
    o = np.zeros((y,x), dtype = np.float64)
    a = np.zeros((y,x), dtype = np.float64)
    b =np.zeros((y,x), dtype = np.float64)
    for ii in range(y):
      for jj in range(x):
        yy = np.asarray(images[:,ii,jj], dtype = np.float64)
        o_sol, a_sol, b_sol = np.linalg.lstsq(A, yy)[0]
        o[ii,jj] = o_sol
        a[ii,jj] = a_sol
        b[ii,jj] = b_sol     
    return o, a, b

  
def Step_correction(images):
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
  (z,y,x) = images.shape
  o = np.zeros((y,x))
  a = np.zeros((y,x))
  b = np.zeros((y,x))
  B = np.linalg.inv(A.T@A)
  C = B @ A.T
  for ii in range(y):
    for jj in range(x):
      yy =np.asarray(images[:,ii,jj], dtype = np.float64)
      o_sol, a_sol, b_sol = C@yy
      o[ii,jj] = o_sol
      a[ii,jj] = a_sol
      b[ii,jj] = b_sol
  return o, a, b