import numpy as np

def create_propagator(n,pixel_size,distance, energy):
    # Fresnel propagator
    # Energy is in keV and distance in cm
    wavelength = 1.23984193/(1000*energy) # in um
    DOD = distance*10**(4) # convert into um
    
    H, W = int(n[0]), int(n[1])

    fs=1/pixel_size
    fx=np.linspace(-fs/2, fs/2-fs/W, W)
    fy=np.linspace(-fs/2, fs/2-fs/H, H)
    FX, FY = np.meshgrid(fx,fx)
    propagator = np.exp(-1j*np.pi*wavelength*DOD*(FX**2+FY**2))

    return propagator


def propagate(Wavefront, pixel_size, distance, energy, padding=0):
    """To avoid artifacts padding is applied"""
    H0, W0 = Wavefront.shape
    #print(H0)
    pad_pixels = padding

    #print(pad_pixels)

    #W = cosine_window_2d(H0) * Wavefront
    #plt.imshow(Wavefront.real)
    #plt.show()
    W = Wavefront
    if pad_pixels > 0:
        Wavefront_padded = padding_wavefront(pad_pixels, W)

    else:
        Wavefront_padded = W

    #plt.imshow(Wavefront_padded[1000:3000,1000:3000].real)
    #plt.show()
    n = Wavefront_padded.shape

    # Evaluate distance
    zmax = zmax_fresnel(n[0], pixel_size, energy)
    #print(zmax)
    num_prop = number_propagations(distance, zmax)
    #num_prop = 1 # For testing purposes, remove later
    sub_distance = distance/num_prop

    U = np.fft.fftshift(np.fft.fft2(Wavefront_padded))
    H = create_propagator(n, pixel_size, sub_distance, energy)
    #print(sub_distance)
    #print(num_prop)
    
    for i in range(num_prop):
        U = H * U
    
    u = np.fft.ifft2(np.fft.ifftshift(U))  # Propagated Wavefront
    if pad_pixels > 0:
        u = u[pad_pixels:-pad_pixels, pad_pixels:-pad_pixels]

    #u = np.fft.ifft2(H*U)  # Propagated Wavefront
    return u

def padding_wavefront(pad_pixels, U):
    #plt.imshow(U.real)
    #plt.show()
    u = np.pad(U, ((pad_pixels, pad_pixels), (pad_pixels, pad_pixels)), mode='edge')
   
    return u


def zmax_fresnel(N, pixel_size, energy):
    wavelength = 1.23984193/(1000*energy) # in um
    zmax = (N * pixel_size * pixel_size) / wavelength
    return zmax * 10**(-4) # convert into cm
def number_propagations(z, zmax):
    if z <= zmax:
        return 1
    return int(np.ceil(z /zmax))
    