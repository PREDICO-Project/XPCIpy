import numpy as np

def cosfunc(t, A, w, p, c):  
  return A * np.cos(w*t + p) + c

def Getting_Phase(Diff_Phase, thickness_sample,G1Period,G2period,zs,z01, wavelength, pixel_size, m,Grating_Phase):
  (y,x) = Diff_Phase.shape
  Phase = np.zeros((y,x))
  if Grating_Phase == 'pi':
    M= 2*G2period/G1Period
    z12 = m*G1Period**2/(8*wavelength)*M
  if Grating_Phase == 'pi_2':
    M= G2period/G1Period
    z12 = m*G1Period**2/(2*wavelength)*M

  if zs<0:
    f = 1+zs/z01
  else: 
    f = 1-zs/z12
  #display_image(thickness_sample)
  
  
  #dx = np.zeros_like(thickness_sample)
  dx = pixel_size
  for jj in range(y):
    phase = 0
    dphase = 0
    for ii in range(x):
      
      #dx[jj,ii] = pixel_size
      phase = Diff_Phase[jj,ii]*dx
      dphase += phase
      Phase[jj,ii] = dphase
  Phase = Phase*G2period/(wavelength*z12*f )
  
  Delta = Getting_delta(Phase,thickness_sample, wavelength)
  return Phase, Delta

def Getting_delta(Phase, thickness, wavelength):

 # thickness and wavelength in um

  (y,x) = thickness.shape
  delta = wavelength*Phase/(2*np.pi*thickness)
  for ii in range(y):
    for jj in range(x):
      if thickness[ii,jj] == 0.0:
        delta[ii,jj]=0
  return delta 

def Getting_beta(Attenuation, thickness, wavelength):
  #% wavelength and thickness in um
  (y,x) = thickness.shape
  beta = wavelength*Attenuation/(4*np.pi*thickness) #% In the Thesis is written: T = exp(2*\frac{2\pi}{\lambda}\beta L)
  for ii in range(y):
    for jj in range(x):
      if thickness[ii,jj] == 0.0:
        beta[ii,jj]=0
  return beta


def DPC_Retrieval(images, images_reference):
  #wavelength = 1.23984193/(1000*energy) # in um
  pixel_size = 1

  o, p, v =FFT_Algorithm(images)
  o_r, p_r, v_r = FFT_Algorithm(images_reference)

  DPC = p-p_r
  DPC = check_limits_DPC(DPC)
 
  DF = v/v_r
  At = -np.log(o/o_r)
  Transmission = o/o_r
  #Phase = Get_Phase(DPC, G2Period,DG1O,DSO, wavelength, pixel_size,DOD)

  return DPC, Transmission, DF


def FFT_Algorithm(images):
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
  Phase = Phase*G2period/(wavelength*z12*f ) 
  return Phase


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


def calculate_sine_parameters(spectrum):
# It calculates the sine parameters using the fourier spectra
  peaks = np.argmax(np.abs(spectrum[1:]))+1
  a = 2*spectrum[peaks].real
  b = 2*spectrum[peaks].imag

  if (a>=0) and (b>=0): 
    phase = np.arctan(b/a)
  if (a<0) and (b>0): 
    phase =np.arctan(b/a)-np.pi 
  if (a<=0) and (b<=0):
    phase =np.arctan(b/a)+np.pi  
  if (a>0) and (b<0):
    phase =np.arctan(b/a) 
  module=np.sqrt(np.power(a,2)+np.power(b,2))
  return phase, module

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