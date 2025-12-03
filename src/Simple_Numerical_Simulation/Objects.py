import numpy as np
from skimage.transform import resize
#import cv2
class GeometricObject():
    def __init__(self,n,pixel_size,delta,beta):
        self.n = n
        self.pixel_size = pixel_size
        self.delta = delta # 2*pi/wavelength * delta
        self.beta = beta # 2*pi/wavelength * beta
        self.projection = []
        self.refr_index = []
    def transmission_function(self, energy):
        wavelength = 1.23984193/(1000*energy) # in um
        projection = self.projection* self.refr_index
        k = 2*np.pi/wavelength
        transmission = np.exp(-1j*k*projection)
        return transmission

    def Obtain_projection(self):
        return self.projection
    
    def Obtain_Phase_Gradient(self, axis):
        projection = self.projection
        projection_gradient = np.gradient(projection, self.pixel_size, axis=axis) #If pixel size is in um, the gradient will be in um^-1
        PG = projection_gradient*self.delta
        return PG

    def a0_Distribution(self):
        projection = self.projection
        beta = self.beta
        transmission = np.exp(-2*projection*beta)
        return transmission

    def Obtain_Phase_Distribuction(self):
        projection = self.projection
        Phase =self.delta*projection
        return Phase
    
    def Obtain_Phase_Laplacian(self):
        projection = self.projection
        projection_gradient_axis0 = np.gradient(projection, self.pixel_size, axis=0) #If pixel size is in um, the gradient will be in um^-1
        projection_gradient_axis1 = np.gradient(projection, self.pixel_size, axis=1) #If pixel size is in um, the gradient will be in um^-1

        #projection_gradient = np.sqrt(projection_gradient_axis0**2 + projection_gradient_axis1**2)
        projection_gradient = projection_gradient_axis0 + projection_gradient_axis1
        projection_gradient2_axis0 = np.gradient(projection_gradient_axis0, self.pixel_size, axis=0) 
        projection_gradient2_axis1 = np.gradient(projection_gradient_axis1, self.pixel_size, axis=1) 

        #projection_gradient2 = np.sqrt(projection_gradient2_axis0**2 + projection_gradient2_axis1**2)
        projection_gradient2 = projection_gradient2_axis0 + projection_gradient2_axis1
        laplacian = -projection_gradient2*self.delta
        return laplacian
    
    def PBI_Theoretical_near_field(self, distance, energy, M):
        '''
        energy in keV
        distance in cm
        Near-Field approximation valid when Fresnel number equal to 1/100 

            F = pixel_size**2/(wavelength * propagation_distance)
        '''
        #distance in cm, energy in keV
        wavelength = 1.23984193 / (energy * 1000) #um
        distance = distance * 10**(4) #um
    
        laplacian = self.Obtain_Phase_Laplacian()
        nx, ny = laplacian.shape
        x, ny = laplacian.shape
        new_width  = int(M * nx)
        new_height = int(M * ny)
        
        laplacian_magnificated = resize(laplacian, (new_height, new_width), order=0, mode="edge", anti_aliasing=False, preserve_range=True)
        #laplacian_magnificated = cv2.resize(laplacian,(int(M*nx),int(M*ny)), interpolation=cv2.INTER_NEAREST)
        intensity_refraction = 1 - distance * wavelength /(2*np.pi*M)*laplacian_magnificated
        intensity_attenuation = self.a0_Distribution()
        intensity_attenuation_magnified = resize(intensity_attenuation, (new_height, new_width), order=0, mode="edge", anti_aliasing=False, preserve_range=True)
        #intensity_attenuation_magnified = cv2.resize(intensity_attenuation,(int(M*nx),int(M*ny)), interpolation=cv2.INTER_NEAREST)
        intensity = intensity_refraction * intensity_attenuation_magnified

        Fresnel_number = self.pixel_size**2/(wavelength*distance)

        print(f"Fresnel number: {Fresnel_number}.")

        return intensity
class Sphere(GeometricObject):
    def __init__(self, n, radius, pixel_size, delta,beta):
        super().__init__(n, pixel_size,delta,beta)
        self.radius = radius
        def make_sphere(n,radius,pixel_size):
            #It returns the thickness of the sphere in any point (valid with a parallel beam).
            x,y = np.mgrid[(-n-0)//2 : (n-0)//2, (-n-0)//2 : (n-0)//2]
            x = (x+0.5)*pixel_size 
            y = (y+0.5)*pixel_size
            image = np.zeros((n,n))
            sph = np.where(x**2+y**2<radius**2)
            image[sph] = 2*np.sqrt(radius**2-x[sph]**2-y[sph]**2)
            return image
        self.projection=make_sphere(n, radius, pixel_size)
                
class Background(GeometricObject):
    def __init__(self, n,pixel_size, delta,beta):
        super().__init__(n, pixel_size,delta,beta)
        self.projection = np.ones((n,n))*beta

class Cylinder(GeometricObject):
    def __init__(self, n, outer_radius,pixel_size, delta,beta, Orientation='Vertical', inner_radius=0):
        super().__init__(n,pixel_size, delta, beta)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.Orientation = Orientation
        def make_cylinder(n,inner_radius,outer_radius, pixel_size, Orientation):
            #It returns the thickness of the sphere in any point (valid with a parallel beam).
            y,x = np.mgrid[(-n-0)//2 : (n-0)//2, (-n-0)//2 : (n-0)//2]
            x = (x+0.5)*pixel_size 
            y = (y+0.5)*pixel_size
            image = np.zeros((n,n))
            if Orientation == 'Vertical':
                r_sq = x**2
            elif Orientation == 'Horizontal':
                r_sq = y**2
            else:
                raise ValueError("Orientation must be 'Vertical' or 'Horizontal'.")
            
            mask_ext = r_sq < outer_radius**2

            if inner_radius == 0.:
                # Solid Cylinder
                image[mask_ext] = 2*np.sqrt(outer_radius**2 - r_sq[mask_ext])
            else:
                "Hollow cylinder"
                mask_int = r_sq < inner_radius**2
                mask_hollow = mask_ext & mask_int

                # Outer region
                image[mask_ext] = 2*np.sqrt(outer_radius**2 - r_sq[mask_ext])

                # Substract inner hollow region
                image[mask_hollow] -= 2*np.sqrt(inner_radius**2 - r_sq[mask_hollow])

                # Ensure no negative thickness
                image[image < 0 ] = 0

            return image
        self.projection=make_cylinder(n, inner_radius, outer_radius, pixel_size,Orientation)
         

class Wedge(GeometricObject):
    def __init__(self, n, width,thickness, pixel_size, delta,beta):
        super().__init__(n,pixel_size, delta, beta)
        self.width = width
        self.thickness = thickness
        def make_wedge(n,width,thickness,pixel_size):
            #It returns the thickness of the sphere in any point (valid with a parallel beam).
            y,x = np.mgrid[(-n-0)//2 : (n-0)//2, (-n-0)//2 : (n-0)//2]
            #x = (x+0.5)*pixel_size 
            #y = (y+0.5)*pixel_size
            image = np.zeros((n,n))
            wedge = np.where((np.abs(x)<width//2) & (np.abs(y)<thickness//2))
            image[wedge] = width//2 - np.abs(x[wedge])
            return image
        
        self.projection=make_wedge(n,  width, thickness,pixel_size)
