import numpy as np
import scipy.ndimage as ndimage 
import os

def obtain_eta(G1Phase):
    if G1Phase == 'pi':
        eta = 2
    if G1Phase == 'pi_2':
        eta = 1
    return eta

def Calculate_Talbot_distance(period, energy):
    # Energy in keV
    wavelength = 1.23984193/(energy*1000)
    Talbot_distance = period**2/(wavelength)*10**-4 # in cm
    return Talbot_distance
    
def Calculate_fractional_Talbot_distance(period, energy, eta):
    # Energy in keV
    wavelength = 1.23984193/(energy*1000)
    Fractional_Talbot_distance = period**2/(2*wavelength*eta**2)*10**-4 #in cm
    return Fractional_Talbot_distance

def noisy(noise_typ,image):
    if noise_typ == "gauss":
      #print(image.shape)
      row,col= image.shape
      mean = 0
      var = 0.001
      sigma = var**0.5
      gauss = np.random.normal(mean,sigma,(row,col))
      gauss = gauss.reshape(row,col)
      noisy = image + gauss
      return noisy

def convert_pixels_to_length(pixels,pixel_size):
    return pixels/pixel_size

def refractive_index_eta(energy, thickness, eta):
    # It returns the parameters of the index of refraction simulating a pi/2 phase
    wavelength = 1.23984193/(1000*energy) # in um
    if eta == 0:
      delta = -1j*1E-6
    else:
      delta = eta* wavelength/(4*thickness)
    return delta
def make_gaussian(shape, pixel_size, FWHM):
    sigma = FWHM/(2*np.sqrt(2*np.log(2))) # In um
    # Gaussian parameters

    X0 = 0
    Y0 = 0
    A = 1
    #fx = (np.linspace(0,n-1,n) - np.ceil((n-1)/2))/n*pixel_size # Spacial frequencies (cycles/um)
    # TODO: Revisar que esté bien definida la gaussiana
    x = np.linspace(0, shape[0]*pixel_size, shape[0])
    y = np.linspace(0, shape[1]*pixel_size, shape[1])
    X, Y = np.meshgrid(x, y)
    gaussian = A *np.exp(-(X-X0)**2/(2*sigma**2))*np.exp(-(Y-Y0)**2/(2*sigma**2))
    
    return gaussian


def gaussian_blurr(image, pixel_size, resolution):
    # The resolution in um.
    shape = image.shape
    gaussian = make_gaussian(shape, pixel_size, resolution)
    gaussianF = (np.fft.fft2(np.fft.fftshift(gaussian)))
    imageF = np.fft.fft2(np.fft.fftshift(image))
    return np.abs(np.fft.ifft2(np.fft.ifftshift((gaussianF*imageF))))


def scipy_gaussian_blur(image, pixel_size, resolution):
    # The resolution in um
    FWHM = resolution/pixel_size
    sigmax = FWHM/(2*np.sqrt(2*np.log(2)))
    image_detector = ndimage.gaussian_filter(image, sigma=sigmax, order=0)
    return image_detector

def thickness_eta(energy, delta, eta):
    # Return the thicness (um) of the object in order to obtain a similar phase shift as pi (eta=2) or pi/2 (eta=1)
    wavelength = 1.23984193/(1000*energy) # in um
    if eta == 1:
        thickness = wavelength/(2*delta)
    elif eta == 2:
        thickness = wavelength/(4*delta)
    return thickness

def thickness_pi_2(energy, delta):
    # It returns the thickness (um) of the object in order to obtain a similar phase shift as pi/2 
    wavelength = 1.23984193/(1000*energy) # in um
    thickness = wavelength/(4*delta)
    return thickness

def thickness_pi(energy, delta):
    wavelength = 1.23984193/(1000*energy) # in um
    thickness = wavelength/(2*delta)
    return thickness

def pi_2(energy, thickness):
    # It returns the parameters of the index of refraction simulating a pi/2 phase
    wavelength = 1.23984193/(1000*energy) # in um
    delta = wavelength/(4*thickness)
    return delta
    
def pi(energy, thickness):
    # It returns the parameters of the index of refraction simulating a pi phase
    wavelength = 1.23984193/(1000*energy) # in um
    delta = wavelength/(2*thickness)
    return delta

def import_material(material):
    # Permits to open and read the txt files inside 'materials_data' folder
    material = material+'.txt'
    file =os.path.join(os.path.dirname(__file__), "materials_data", material)
    return np.loadtxt(file)

def closest_to(list, value):
    # It returns the position of the closest value in a list to the reference value
    list = np.asarray(list)
    position = (np.abs(list-value)).argmin()
    return position

def interpolate(x,x0,x1,y0,y1):
    # Linear interpolation to obtain delta and beta values from the txt file
    y = y0+(y1-y0)*(x-x0)/(x1-x0)
    return y

def read_file(filename):
    filename = filename+'.txt'
    file = os.path.join(os.path.dirname(__file__), "input", filename)
    #file = pd.read_csv(file, sep="\t", header=None)
    file_lines ={}
    with open(file, 'r') as f:
        lines = f.readlines()
    count = 0
    for line in lines:
        line = line.strip('\n')
        file_lines[count] = line
        count +=1
    f.close()
    return file_lines

def convolve(psf, image):
    I = np.fft.fft2(np.fft.ifftshift(image))  
    PSF = np.fft.fft2(np.fft.ifftshift(psf))
    image_conv = np.fft.fftshift(np.fft.ifft2(I*PSF)).real  
    return image_conv

def check_grating_sampling(period_px):
    print(period_px)
    if (period_px / 2) % 1 != 0:  
        print(
            f"WARNING: The half of the period of the grating ({period_px/2:.2f} px) is not an even number of pixels, the gratings may not be symmetrical.")

def check_phase_stepping(n_steps, period_px, step_size_px):

    total_shift = n_steps * step_size_px
    print(total_shift)
    if total_shift < period_px * (1-1e-3):
        print(
            f"WARNING: The number of steps ({n_steps}) with step size ({step_size_px:.2} px) does not cover a full period of the grating ({period_px:.2f} px)."
        )
    elif np.isclose(total_shift % period_px, 0) is False:
        print(
            f"WARNING: The total number of steps ({total_shift:.2f} px) is not an exact multiple of the G2 period ({period_px:.2f} px). Errors in the reconstruction can appear.")
