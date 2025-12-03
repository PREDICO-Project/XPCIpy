import numpy as np
import os
import tifffile as tif
from PIL import Image
import scipy.fftpack as fftpack
from scipy.ndimage import generic_filter

try:
    from numba import jit
except Exception as err:
    #print(f'Numba cannot be imported: {err}')
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

"""
In this file there are some useful functions to make different calculations.

Author: Víctor Sánchez Lara
Date: April 2022  
"""
@jit(nopython=True, parallel=False, cache=True)
def cosfunc(t, A, w, p, c):  
  return A * np.cos(w*t + p) + c

@jit(nopython=True, parallel=False, cache=True)
def numerical_integration(image, dx):
    """
    Function to obtain the Phase from the Phase Gradient image. It uses the numerical integration.

    Args:
        image (numpy array): Phase Gradient Image
        dx (float): Pixel Size (microns)

    Returns:
        numpy array: Integrated Phase.
    """
    # Function to make the analytical integration along x-direction.
    (y,x) = image.shape
    Phase = np.zeros((y,x))
    for jj in range(y):
        dphase = 0
        for ii in range(x):
            phase = image[jj,ii]*dx
            dphase += phase
            Phase[jj,ii] = dphase
    return Phase

@jit(nopython=True, parallel=False, cache=True)
def Get_Phase(Diff_Phase, G2period,zs,z01, wavelength, pixel_size,distance):
  """
  Function to calculate the Phase using the Phase Gradient Image and experimental information.

  Args:
      Diff_Phase (numpy array): Phase Gradient Image
      G2period (float): Period of G2 grating (microns)
      zs (float): Distance between the sample and G1 (cm)
      z01 (float): Distance between G0 and G1 (cm)
      wavelength (float): Wavelength of design (microns)
      pixel_size (float): pixel size (microns)
      distance (float): Distance between G1 and G2 (cm)

  Returns:
      numpy array: Phase Image
  """
  
  z12 = distance*10**4 # In um
  zsample =zs*10**4 #In um
  z01um = z01*10**4
  if zs<0:
    f = 1+zsample/z01um
  else: 
    f = 1-zsample/z12
  Phase = numerical_integration(Diff_Phase, pixel_size)
  #Phase = Phase*G2period/(wavelength*z12*f ) 
  return Phase

@jit(nopython=True, parallel=False, cache=True)
def check_limits_DPC(DPC):
    """
    Function to secure that the Phase Gradient value is in the range [-pi,pi]

    Args:
        PG (numpy array): Phase Gradient Image

    Returns:
        numpy array: Phase Gradient Image
    """
    (y,x) = DPC.shape
    for ii in range(y):
        for jj in range(x):
            if DPC[ii,jj]>np.pi:
                DPC[ii,jj] -=2*np.pi
            if DPC[ii,jj]<-np.pi:
                DPC[ii,jj] +=2*np.pi
    return DPC

def read_Tiff_file(name):
  """
  Function to open and read tiff files. To be able to read the images, they must be located in "Data" folder.

  Args:
      name (string): name of the file to read without ".tif"

  Returns:
      numpy array: Image
  """
  try:
    path_1 = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    path_2 = os.path.abspath(os.path.join(path_1, os.pardir))
    path_to_Data = os.path.join(path_2, 'Data')
    file_images =os.path.join(path_to_Data, name+'.tif')
  except:
    file_images = os.path.abspath(name)
    
  image = tif.imread(file_images)
  return image

def save_results(filename_images,Diff_Phase,attenuation,Dark_Field,Phase):
  stack = []
  stack.append(Diff_Phase)
  stack.append(attenuation)
  stack.append(Dark_Field)
  stack.append(Phase)
  stack = np.asarray(stack)
  tif.imwrite(os.path.join(os.path.dirname(os.path.dirname(__file__)), "Output",)+'/'+filename_images+'_results.tif', 
  stack, photometric='minisblack')
  
def save_image(image, filename):
  im = Image.fromarray(image)
  sv = im.save(filename)
  
  
  
@jit(nopython=True, parallel=False, cache=True)
def calculate_sine_parameters(spectrum):
# It calculates the sine parameters using the fourier spectra
  peaks = np.argmax(np.abs(spectrum[1:]))+1
  a = 2*spectrum[peaks].real
  b = 2*spectrum[peaks].imag
  if (a>0) and (b>0): 
    phase = np.arctan(b/a)
  if (a<0) and (b>0): 
    phase =np.arctan(b/a)-np.pi 
  if (a<0) and (b<0):
    phase =np.arctan(b/a)+np.pi  
  if (a>0) and (b<0):
    phase =np.arctan(b/a) 
  module=np.sqrt(np.power(a,2)+np.power(b,2))
  return phase, module

@jit(nopython=True, parallel=False, cache=True)
def calculate_visibility(amplitude,offset):
  """
  Function to calculate the visibility given the amplitude and the offset

  Args:
      amplitude (numpy array): Array with the amplitude value at each pixel
      offset (numpy array): Array with the offset value at each pixel

  Returns:
      numpy array: Array with the visibility value at each pixel
  """
  return amplitude/offset       

def apply_FF_DF_correction(images, FF_image, DF_image):
  """
  Function to perform the Flat Field and Dark Field corrections. 

  Args:
      images (numpy array): Images to be corrected
      FF_image (numpy array): Flat Field Image
      DF_image (numpy array): Dark Field Image

  Returns:
      numpy array: Corrected Images
  """
  images_corrected = (images - DF_image)/(FF_image - DF_image)
  return images_corrected

def calculate_guess_freq(tt, yy):
  """
  Function to calculate the guessed frequency to make the curve fitting.

  Args:
      tt (numpy array): _description_
      yy (numpy array): _description_

  Returns:
      numpy array: guessed frequency
  """
  ff = np.fft.fftfreq(len(tt), (tt[1]-tt[0]))   # assume uniform spacing
  Fyy = abs(np.fft.fft(yy))
  guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   # excluding the zero frequency "peak", which is related to offset
  #guess_freq = 1/2.*np.pi
  return guess_freq

@jit(nopython=True, parallel=False, cache=True)
def calculate_guess_amp_offset(yy):
  """
  Function to calculate the guess amplitud and offset to make the curve fitting.

  Args:
      yy (numpy array): Array

  Returns:
      numpy array: guess amplitude
      numpy array: guess offset
  """
  guess_amp = np.std(yy) * 2.**0.5
  guess_offset = np.mean(yy)
  return guess_amp,guess_offset

@jit(nopython=True, parallel=False, cache=True)
def check_amp_phase(A, p):
  """
  Function to check if the Amplitude is negative. If it is, then change the phase value.
  Also check if phase value is in the range [-pi,pi]

  Args:
      A (numpy array): Array with the Amplitude values
      p (numpy array): Array with the Phase values

  Returns:
      numpy array: Array with modified Amplitude values
      numpy array: Array with modified Phase values
  """
  if A<0:
    A = np.abs(A)
    p -=np.pi
  if p>(np.pi):
    p=p-2*np.pi
  if p<(-1*np.pi):
    p=p+2*np.pi
  return A,p

@jit(nopython=True, parallel=False, cache=True)
def calculate_phase(a,b):
  """
  Function to calculate the phase from the real and imaginary part of a complex number.
  The last part is important to avoid the phase wrapping. 

  Args:
      a (numpy array): Imaginary part of the complex number
      b (numpy array): Real part of the complex number

  Returns:
      numpy array: Angle of the complex number
  """
  (y,x) = b.shape
  phase = np.arctan(a/b)
  for ii in range(y):
    for jj  in range(x):
      if (b[ii,jj]<0) and (a[ii,jj]>0): 
        phase[ii,jj] =phase[ii,jj]+np.pi 
      if (b[ii,jj]<0) and (a[ii,jj]<0):
        phase[ii,jj] =phase[ii,jj]-np.pi  
  return phase


def fill_zero_values(image):
  indices = np.argwhere(image == 0)
  for indice in indices:
    image[indice[0],indice[1], indice[2]] = (image[indice[0],indice[1], indice[2]+1] + image[indice[0],indice[1], indice[2]-1])/2   
  return image

def apply_FF_DF_correction(images, FF_image, DF_image):
  """
  Function to perform the Flat Field and Dark Field corrections. 

  Args:
      images (numpy array): Images to be corrected
      FF_image (numpy array): Flat Field Image
      DF_image (numpy array): Dark Field Image

  Returns:
      numpy array: Corrected Images
  """
  images_corrected = (images - DF_image)/(FF_image - DF_image)
  return images_corrected

def Apply_Phase_Wiener_filter(DPC, x_pixel_size, y_pixel_size, v0, n, s):
  """
  Function to calculate the integrated phase from the Differential Phase Contrast (DPC) Image usinga Wiener filter following [1]. The Wiener filter
  reduces the noise contribution when the integration of the DPC Image is performed. 
  
  [1]: Massimi, L., Buchanan, I., Astolfo, A., Endrizzi, M., & Olivo, A. (2020). 
  Fast, non-iterative algorithm for quantitative integration of X-ray differential phase-contrast images. 
  Optics express, 28(26), 39677–39687. https://doi.org/10.1364/OE.405755

  Args:
      DPC (numpy array): Differential Phase Contrast Image
      x_pixel_size (float): pixel size in x-direction (um)
      y_pixel_size (float): pixel size in y-direction (um)
      v0 (float): vertical cutoff frequency (um^-1)
      n (integer): 1 or 2
      s (float): Number to estimate the SNR

  Returns:
      numpy array: Integrated Phase Image
  """

  

  Ny = DPC.shape[0]
  Nx = DPC.shape[1]
 
  fx=np.linspace(-Nx//2, Nx//2-1, Nx)/Nx/x_pixel_size
  fy=np.linspace(-Ny//2, Ny//2-1, Ny)/Ny/y_pixel_size
  #fx=np.linspace(0, Nx, Nx)/x_pixel_size/Nx
  #fy=np.linspace(0, Ny, Ny)/y_pixel_size/Ny
  #fx = np.fft.fftfreq(Nx, d= x_pixel_size)
  #fy = np.fft.fftfreq(Ny, d= y_pixel_size)
  
  #fx = np.fft.fftfreq(n)/pixel_size 
  FX, FY = np.meshgrid(fx,fy)
  hann_window_x = np.hanning(Nx)
  hann_window_y = np.hanning(Ny)

  hann_window = np.outer(hann_window_y, hann_window_x)
  #DPC = DPC * hann_window 
  #DPC = gaussian_filter(DPC, sigma=1)
  
  '''Analytical estimation of SNR as a function of the spatial frequency. The filter is done just in the Y-direction, where the patterns
  due to the noise appears (because the integration is done in the X-direction).'''
  SNR = s/( 1 + (FY/v0) **(2 * n))
  #SNR = s*np.exp(-2*np.pi**2*v0**2*(FX**2 + FY**2))
  #SNR = 1e7
  SNR_inverse = 1 / SNR
  
  D = 2*1j*np.sin(np.pi*x_pixel_size*FX)
  D_conjugated = np.conj(D)
  D_2 = np.abs(D)**2
 
  Fourier_theta = fftpack.fftshift(fftpack.fft2(DPC))
  #plt.imshow(np.real(np.fft.ifft2(np.fft.ifftshift(Fourier_theta)))-DPC)
  #plt.colorbar()
  #plt.show()
                                
  Wiener_filter = D_conjugated/(D_2+SNR_inverse+1e-8)
  #plt.imshow(np.abs(Wiener_filter)**2)
  #plt.colorbar()
  #plt.show()

  #plt.plot(np.abs(Wiener_filter[500,500:550])**2)
  #plt.plot(np.abs(D[500,500:550])**2)
  #plt.yscale('log')
  #plt.show()

  Phase = (fftpack.ifft2(fftpack.ifftshift(Wiener_filter*Fourier_theta)))*x_pixel_size
  #Phase,_ = restoration.unsupervised_wiener(DPC, D)
  Phase = np.real(Phase)
  return Phase

def fill_nans(image, size=3):
  
    if np.isfinite(image).all():
        return image
      
    mask = ~np.isfinite(image)

    def nanmean_filter(window):
        vals = window[np.isfinite(window)]
        if vals.size == 0:
            return 0.0
        return vals.mean()

    filled = generic_filter(image, nanmean_filter, size=size, mode="nearest")
    image[mask] = filled[mask]
    return image
  
def fill_nans_zero(image):
    """
    Faster version of fill_nans that only fills NaN/Inf with zeros.
    """
    image = np.asarray(image)

    if np.isfinite(image).all():
        return image
      
    out = image.astype(float, copy=True)
    mask = ~np.isfinite(out)
    out[mask] = 0.0
    return out