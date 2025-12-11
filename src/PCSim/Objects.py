import numpy as np
from src.PCSim.material import make_material
from scipy.ndimage import rotate
import warnings

class GeometricObject():
    def __init__(self, n, pixel_size, material, DSO,
                 x_shift_px=0, y_shift_px=0):
        self.n = int(n)
        self.pixel_size_init = float(pixel_size)
        self.material = material
        self.DSO = DSO
        self.x_shift_px = int(x_shift_px)
        self.y_shift_px = int(y_shift_px)

    

    def transmission_function(self, energy, pixel_size):
        """
        Compute complex transmission at the current plane sampling.

        Parameters
        ----------
        energy : float
            Photon energy (keV).
        pixel_size : float
            Current pixel size (same distance units as geometry; typically µm).

        Returns
        -------
        transmission : (n, n) complex ndarray
        """
        wavelength = 1.23984193 / (1000 * energy)  # µm
        k = 2.0 * np.pi / wavelength  # 1/µm

        refr_index_term = self.set_refr_index(energy)

        proj = self.make_geometry(self.n, pixel_size)

        refractive_index_projection = proj * refr_index_term
        transmission = np.exp(-1j * k * refractive_index_projection)
        return transmission

    def set_refr_index(self, energy):
        return make_material(self.material, energy)

    def make_geometry(self, n, pixel_size):
        raise NotImplementedError("Subclasses must implement make_geometry().")
        
class Sphere(GeometricObject):
    def __init__(self, n, radius, pixel_size, material, DSO, x_shift_px=0, y_shift_px=0):
        super().__init__(n, pixel_size, material, DSO, x_shift_px=x_shift_px, y_shift_px=y_shift_px)
        
        self.radius = float(radius)

    def make_geometry(self, n, pixel_size):

        y,x = np.mgrid[(-n-self.y_shift_px)//2 : (n-self.y_shift_px)//2, (-n-self.x_shift_px)//2 : (n-self.x_shift_px)//2]

        x = (x+0.5)*pixel_size 
        y = (y+0.5)*pixel_size

        r2 = x**2 + y**2
        R2 = self.radius ** 2
        thickness = np.zeros((n, n), dtype=float)
        inside = r2 < R2
        thickness[inside] = 2.0 * np.sqrt(np.maximum(R2 - r2[inside], 0.0))
        return thickness
       
class Wedge(GeometricObject):
    def __init__(self, n, width, thickness, pixel_size, material, DSO, x_shift_px=0, y_shift_px=0):
        super().__init__(n, pixel_size, material, DSO, x_shift_px=x_shift_px, y_shift_px=y_shift_px)
        
        self.width = width
        self.thickness = thickness
        
    def make_geometry(self, n, pixel_size):
        width = self.width
        thickness = self.thickness
        x_shift = self.x_shift_px
        y_shift = self.y_shift_px
        #It returns the thickness of the sphere in any point (valid with a parallel beam).
        y,x = np.mgrid[(-n-y_shift)//2 : (n-y_shift)//2, (-n-x_shift)//2 : (n-x_shift)//2]
        x = (x+0.5)*pixel_size 
        y = (y+0.5)*pixel_size
        image = np.zeros((n,n))

        half_width = width / 2
        wedge_mask = np.abs(x) < half_width
        image[wedge_mask] = (half_width-np.abs(x[wedge_mask]) / half_width * thickness)
        
        return image
        
               
class Cylinder(GeometricObject):
    def __init__(self, n, outer_radius, inner_radius,Orientation,pixel_size, material, DSO, x_shift_px=0, y_shift_px=0):
        super().__init__(n, pixel_size, material, DSO, x_shift_px=x_shift_px, y_shift_px=y_shift_px)
  
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.Orientation = Orientation

    def make_geometry(self, n, pixel_size):
        #It returns the thickness of the sphere in any point (valid with a parallel beam).
    
        x_shift = self.x_shift_px
        y_shift = self.y_shift_px
        outer_radius = self.outer_radius
        inner_radius = self.inner_radius
        Orientation = self.Orientation
        
        y,x = np.mgrid[(-n-y_shift)//2 : (n-y_shift)//2, (-n-x_shift)//2 : (n-x_shift)//2]
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
         
        
class Substrate():
    def __init__(self, n, pixel_size, thickness,material):
        self.n = n 
        self.pixel_size = pixel_size
        self.thickness = thickness
        self.material=material
        self.energy = 0
        self.refr_index = 0 # Refractive Index $n = \delta-i\beta$            
        self.object = self.make_substrate()
        
    def make_substrate(self):
            substrate = np.ones((self.n,self.n))
            return substrate*self.thickness        
        
class Grating(GeometricObject):
    def __init__(self, n, period, DC, pixel_size, material, DSO, thickness_um=None, grating_type='custom', angle = 0,x_shift_px=0, y_shift_px=0, step =0, design_energy=None):
        super().__init__(n, pixel_size, material, DSO, x_shift_px=x_shift_px, y_shift_px=y_shift_px)

        self.period = period
        self.DC = DC
        self.step = step
        self.grating_type = grating_type
        self.angle = angle
        self.design_energy = design_energy
        
        self.thickness = thickness_um
   
        self.check_grating_sampling()
        #self.projection = self.make_geometry()

        #self.object = self.movable_Grating()   

    def transmission_function(self, energy, pixel_size):
        if self.grating_type in ['phase_pi', 'phase_pi_2']:
            phi = np.pi if self.grating_type == 'phase_pi' else (0.5*np.pi)
            mask = self.movable_Grating(self.n, pixel_size, self.step)
            return np.exp(-1j * phi * mask)

        return super().transmission_function(energy, pixel_size)
    
    def make_binary_grating(self, n, pixel_size):
        period = self.period
        step = self.step
        DC = self.DC
        #% It returns a binary grating 
        out_original = np.zeros((n, n))
        out = np.zeros((n, n))
        period_px = int(np.round(period / pixel_size)) #In pixels
        
        not_zeros = int(DC * period_px)
        zeros = int((1-DC) * period_px)
        #print(not_zeros)
        #print(zeros)
        #print(period_px//2)
        for i in range(-not_zeros, zeros):
        #for i in range(-period_px//2,period_px//2):
            #print(i)
            if i<0:
                i=i+period_px
                out[:,(i)::period_px] = 1
        return out
    
    def movable_Grating(self, n, pixel_size, step_um):
        H = W = int(n)
        px = float(pixel_size)
        mask = self.make_binary_grating(H, px)
        
        shift_px = step_um / px
        #print(shift_px)
        mask = self.fourier_shift_x(mask, shift_px)

        if self.x_shift_px:
            mask = np.roll(mask, int(self.x_shift_px), axis=1)
        if self.y_shift_px:
            mask = np.roll(mask, int(self.y_shift_px), axis=0)

        if self.angle != 0:
            pad = int(np.ceil(np.sqrt(2) * H - H) / 2)
            m2 = np.pad(mask, ((pad, pad), (pad, pad)), mode='wrap')
            m2 = rotate(m2, self.angle, reshape=False, order=0, mode='wrap')
            mask = m2[pad:pad+H, pad:pad+W]

        return mask
    
    def fourier_shift_x(self, image, shift_px):
        """Shift an image in x by a fractional number of pixels using Fourier shift theorem."""
        if shift_px == 0:
            return image
        H, W = image.shape
        fx = np.fft.fftfreq(W)
        fy = np.fft.fftfreq(H)
        FX, FY = np.meshgrid(fx, fy)
        shift_phase = np.exp(-2j * np.pi * FX * shift_px)
        image_ft = np.fft.fft2(image)
        shifted_image = np.fft.ifft2(image_ft * shift_phase).real
        return  np.clip(shifted_image, 0.0, 1.0)    
    
    def make_geometry(self, n, pixel_size):
        if self.grating_type in ['phase_pi', 'phase_pi_2']:
            
            return np.zeros((n, n), dtype=np.float32)
        return self.thickness * self.movable_Grating(n, pixel_size, self.step)

    def update_step(self, new_step):
        self.step = new_step
        #self.projection = self.make_geometry(self.n, self.pixel_size_init)

    def get_Talbot_distance(self):
        wavelength = 1.23984193/(1000*self.design_energy)
        Talbot_distance = (2*self.period**2/ wavelength) * 10**(-4) #cm
        return Talbot_distance

    def check_grating_sampling(self):
        """
        Sampling condition for gratings. To avoid aliasing, 5-6 pixel per period are recommended, but not strictly necessary.
        """
        if self.pixel_size_init > self.period/6:
            warnings.warn(f"[Grating sampling warning] Pixel size ({self.pixel_size_init:.3g}) may be too large compared to grating period ({self.period:.3g}). Please consider to reduce the pixel size or increase the grating period.")

class DoubleSlit(GeometricObject):

    def __init__(self, n, slit_width, center_distance, screen_thickness, pixel_size, material, DSO, slit_height=None,x_shift_px=0, y_shift_px=0):
        super().__init__(n, pixel_size, material, DSO,
                         x_shift_px=x_shift_px, y_shift_px=y_shift_px)
        self.slit_width = slit_width
        self.center_distance = center_distance
        self.screen_thickness = screen_thickness
        self.slit_height = None if slit_height is None else slit_height

    def make_geometry(self, n, pixel_size):
        y, x = np.mgrid[(-n - self.y_shift_px)//2 : (n - self.y_shift_px)//2, (-n - self.x_shift_px)//2 : (n - self.x_shift_px)//2]

        x = (x + 0.5) * pixel_size
        y = (y + 0.5) * pixel_size

        img = np.full((n, n), self.screen_thickness, dtype=float)
        
        half_d = 0.5 * self.center_distance
        half_w = 0.5 * self.slit_width

        mask_left_x  = np.abs(x + half_d) <= half_w
        mask_right_x = np.abs(x - half_d) <= half_w

        if self.slit_height is None:
            mask_y = np.ones_like(y, dtype=bool)   # rendijas a lo largo de todo Y
        else:
            mask_y = np.abs(y) <= (0.5 * self.slit_height)

        slit_mask = (mask_y & (mask_left_x | mask_right_x))
        single_slit = (mask_y & mask_left_x)
        img[slit_mask] = 0.0
        #img[single_slit] = 0.0

        return img
class KnifeEdge(GeometricObject):

    def __init__(self, n, pixel_size, material, DSO, orientation='vertical', blocked_side='left', screen_thickness=50.0, edge_offset_um=0.0, x_shift_px=0, y_shift_px=0):
        super().__init__(n, pixel_size, material, DSO, x_shift_px=x_shift_px, y_shift_px=y_shift_px)
        self.orientation = orientation.lower()
        self.blocked_side = blocked_side.lower()
        self.screen_thickness = screen_thickness
        self.edge_offset_um = edge_offset_um

        if self.orientation not in ('vertical', 'horizontal'):
            raise ValueError("orientation must be 'vertical' or 'horizontal'.")
        if self.orientation == 'vertical' and self.blocked_side not in ('left', 'right'):
            raise ValueError("blocked_side for orientation='vertical' must be 'left' or 'right'.")
        if self.orientation == 'horizontal' and self.blocked_side not in ('up', 'down'):
            raise ValueError("blocked_side for orientation='horizontal' must be 'up' or 'down'.")

    def make_geometry(self, n, pixel_size):
        y, x = np.mgrid[(-n - self.y_shift_px)//2 : (n - self.y_shift_px)//2, (-n - self.x_shift_px)//2 : (n - self.x_shift_px)//2]
        x = (x + 0.5) * pixel_size
        y = (y + 0.5) * pixel_size

        thickness = np.zeros((n, n), dtype=float)

        if self.orientation == 'vertical':
            if self.blocked_side == 'left':
                mask = (x < self.edge_offset_um)
            else:
                mask = (x > self.edge_offset_um)
        else:
            if self.blocked_side == 'down':
                mask = (y < self.edge_offset_um)
            else:
                mask = (y > self.edge_offset_um)

        thickness[mask] = self.screen_thickness
        return thickness
