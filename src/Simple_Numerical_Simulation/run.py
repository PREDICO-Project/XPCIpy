import numpy as np
import Objects as obj
#import imageio
import simulation as sim
import tifffile as tiff
n = 1024
radius = 300 # um
pixel_size = 1 #um
delta = 1E-2 # Real part of refractive index multiplied by 2*pi/wavelength
beta = 1E-6 # The imaginary part  of refractive index multiplied by 2*pi/wavelength
noise_mean = 0.00
error_steps_mean = 0.00
error_dose_mean = 0.00
Moire = False
Sphere = obj.Sphere(n, radius, pixel_size, delta, beta)

Sphere_PG = Sphere.Obtain_Phase_Gradient()
Sphere_Phase = Sphere.Obtain_Phase_Distribuction()
Sphere_a0 = Sphere.a0_Distribution()


Images, Images_reference = sim.Simulation(Sphere, 20, noise_mean, error_steps_mean, error_dose_mean, Moire)
Images = np.asarray(Images)
Images_reference = np.asarray(Images_reference)
#print(Images)
Images *= 400
Images_reference *= 400
filename_object_images = 'All_images'
filename_reference_images = 'All_images_reference'
tiff.imwrite('Simple_Numerical_Simulation/Simulation/'+str(filename_object_images)+'.tif', Images.astype(np.uint16))
tiff.imwrite('Simple_Numerical_Simulation/Simulation/'+str(filename_reference_images)+'.tif', Images_reference.astype(np.uint16))
#imageio.volwrite('Simple_Numerical_Simulation/Simulation/'+str(filename_object_images)+'.tif', Images)
#imageio.volwrite('Simple_Numerical_Simulation/Simulation/'+str(filename_reference_images)+'.tif', Images_reference)
#images=io.imread('images.tif')