import numpy as np
from skimage.restoration import unwrap_phase as unwrap

import src.TLRec.Fits as fit
import src.TLRec.utils as utils


""" This directory has the function that will be used to do the phase retrieval on experimental images.
 You will need to load the stack of images, the periods of the gratings (in um), the distance between the source and the 
 object (in cm), the distance between the object and G2 (in cm), the effective energy of the X-ray spectrum and 
 the multiple of the Talbot distance between G1 and G2. """
 
def Get_parameters(Imax, Imin):
  '''
  Return a_0 and a_1
  '''
  a0 = (Imax+Imin)/2
  a1 = (Imax-Imin)/2
  return a0, a1

def Two_Shots_Reconstruction(images, images_reference):
  '''
  Function to retrieve the dark field and attenuation images using the two shots approximation. 
  This method is based on Ref[1].
  
  The Intensity modulation function: I = a_0 + a_1*cos(2*pi*x/p2 + phi) is evaluated at
  x1 = 0 and x2 = p2/2. When the phase (phi) is low, a Taylor expansion of the Intensity Modulation Function 
  at these points yields the following expressions. 
  
  I1 = a_0+a_1 and I2 = a_0-a_1. 

  Input:
  -------------------------------------------------------------
  images: 3 dimensional array with the object images.
  images_reference:  3 dimensional array with the reference images.
  ---------------------------------------------------------------
  Return: 
  ---------------------------------------------------------------
  Dark_Field: numpy array
  Transmission: numpy array
  ---------------------------------------------------------------
  [1] https://doi.org/10.1364/OE.24.027032
  '''
  Imax = images[0]
  Imin = images[1]
  Imax_ref = images_reference[0]
  Imin_ref = images_reference[1]

  a0, a1 = Get_parameters(Imax, Imin)
  a0_ref, a1_ref = Get_parameters(Imax_ref, Imin_ref)

  v = a1/a0
  v_ref = a1_ref/a0_ref
  Dark_Field = v/v_ref
  At = -np.log(a0/a0_ref)
  Transmission = a0/a0_ref
  return Dark_Field, Transmission

def Modulation_Curve_Reconstruction(images, images_reference,G2Period,DSO, DOD, DG1O, energy, pixel_size,type, unwrap_phase = False):
  '''
  Function to perform the Modulation Curve Reconstruction (or Phase Stepping Curve, PSC) from the experimental data.

  I1 = a_0+a_1 and I2 = a_0-a_1. 

  Args:
      images (numpy array): 3 dimensional array with the raw images recorded by the detector with the object. The shape should be
        (N, Y, X) where N is the number of phase steps, Y is the number of pixels in the vertical orientation and X 
        the number of pixels in the horizontal orientation.
      images_reference (numpy array): 3 dimensional array with the raw images recorded by the detector without the object.
      G2Period (float): Period of G2 grating in microns (\mu m)
      DSO (float): Distance Source-Object in cm
      DOD (float): Distance Object-Detector in cm
      DG10 (float): Distance G1-Object in cm
      energy (float): Eenrgy of design in keV
      type (string): Name of reconstruction method to be applied
      unwrap_phase (boolean): True if unwrap phase algorithm from skimage want to be done

  Returns:
      DPC (numpy array): Differential Phase Contrast Image
      Abs (numpy array): Absorption Image defined as -ln(I0,obj/I0,ref)
      Transmission (numpy array): Transmission Image defined as (I0,obj/I0,ref)
      DF (numpy array):  Dark Field Image defined as (Vobj/Vref)
      Phase (numpy array): Phase Image defined as the direct integration of the DPC image.
      Phase_Stepping_Curve_reference (numpy array): Phase of the reference PSC 
      Phase_Stepping_Curve_object (numpy array): Phase of the object PSC
  '''
  
  
  wavelength = 1.23984193/(1000*energy) # in um
  try:
    (z,y,x) = images.shape 
    (zr, yr,xr) = images_reference.shape
  except:
    raise Exception('The images need to be 3 dimensional (z, y, x) with z equal to the number of phase steps and (y,x) the size of a single image')
  
  if type == 'FFT':
    o, p, v =fit.fit_fft(images)
    o_r, p_r, v_r = fit.fit_fft(images_reference)
    
  elif type == 'Fast_FFT':
    o, p, v =fit.fastest_fit_fft(images)
    o_r, p_r, v_r = fit.fastest_fit_fft(images_reference)
 
    
  elif type == 'least_squares':
    steps = np.arange(0,images.shape[0],1)*2*np.pi/images.shape[0]
    steps_r = np.arange(0,images_reference.shape[0],1)*2*np.pi/images_reference.shape[0]
    A  = np.vstack([np.ones(len(steps)), np.cos(steps), np.sin(steps)]).T
    A = np.asarray(A, dtype = np.float64)
    A_r  = np.vstack([np.ones(len(steps_r)), np.cos(steps_r), np.sin(steps_r)]).T
    A_r = np.asarray(A_r, dtype = np.float64)
    o, a, b =fit.opt_fit_least_square(images, A)
    o_r, a_r, b_r =fit.opt_fit_least_square(images_reference, A_r)
    p = utils.calculate_phase(a,b)
    p_r = utils.calculate_phase(a_r,b_r)
    v = np.sqrt(a**2+b**2)/o
    v_r = np.sqrt(a_r**2+b_r**2)/o_r
  
  elif type == 'fast_lstsq':
    steps = np.arange(0,images.shape[0],1)*2*np.pi/images.shape[0]
    steps_r = np.arange(0,images_reference.shape[0],1)*2*np.pi/images_reference.shape[0]
    A  = np.vstack([np.ones(len(steps)), np.cos(steps), np.sin(steps)]).T
    A = np.asarray(A, dtype = np.float64)
    A_r  = np.vstack([np.ones(len(steps_r)), np.cos(steps_r), np.sin(steps_r)]).T
    A_r = np.asarray(A_r, dtype = np.float64)
    o, a, b =fit.resolve_eq(images, A)
    o_r, a_r, b_r =fit.resolve_eq(images_reference, A_r)
    p = utils.calculate_phase(a,b)
    p_r = utils.calculate_phase(a_r,b_r)
    v = np.sqrt(a**2+b**2)/o
    v_r = np.sqrt(a_r**2+b_r**2)/o_r
    
  elif type == 'Step_correction':
    o, a, b, steps =fit.Step_correction(images)
    o_r, a_r, b_r, steps_r =fit.Step_correction(images_reference)
    p = utils.calculate_phase(a,b)
    p_r = utils.calculate_phase(a_r,b_r)
    v = np.sqrt(a**2+b**2)/o
    v_r = np.sqrt(a_r**2+b_r**2)/o_r
  
  else:
    raise Exception('Not reconstruction type selected properly, try FFT, least_squares...')  
  
  """ Unwrap the phase using the scikit library. However, the utils.check_limits_PG should be enough 
   to remove artifacts due the wrapping of the phase """
  if unwrap_phase:
    """The code could be more slow."""
    p = unwrap(p)
    p_r = unwrap(p_r)
    DPC = p-p_r
  else:
    DPC = p-p_r
    DPC = utils.check_limits_DPC(DPC) 
    
  DF = v/v_r
  #Abs = -np.log(o/o_r)
  Transmission = o/o_r
  
  DPC = utils.fill_nans_zero(DPC)
  DF = utils.fill_nans_zero(DF)

  Transmission = utils.fill_nans_zero(Transmission)
  
  Phase = utils.Get_Phase(DPC, G2Period,DG1O,DSO, wavelength, pixel_size,DOD)
  Phase_Stepping_Curve_reference = p_r
  Phase_Stepping_Curve_reference = utils.check_limits_DPC(Phase_Stepping_Curve_reference)
  Phase_Stepping_Curve_object = p
  Phase_Stepping_Curve_object = utils.check_limits_DPC(Phase_Stepping_Curve_object)
  return DPC, Transmission, DF, Phase, Phase_Stepping_Curve_reference, Phase_Stepping_Curve_object





