import numpy as np
from src.PCSim.material import make_material
from scipy.ndimage import rotate
import warnings

class GeometricObject():
    def __init__(self, n, pixel_size, material, DSO,
                 x_shift=0, y_shift=0):
        self.n = int(n)
        self.pixel_size_init = float(pixel_size)
        self.material = material
        self.DSO = DSO
        self.x_shift = float(x_shift)  # physical units (um)
        self.y_shift = float(y_shift)  # physical units (um)
        self.transmission_cache = {}

    def grid(self, n, pixel_size, center=(0.0, 0.0)):
        x_shift_px = round(self.x_shift / pixel_size)
        y_shift_px = round(self.y_shift / pixel_size)
        y, x = np.mgrid[-n//2 + y_shift_px : n//2 + y_shift_px, -n//2 + x_shift_px : n//2 + x_shift_px]
        x = (x + 0.5) * pixel_size - float(center[0])
        y = (y + 0.5) * pixel_size - float(center[1])
        return x, y

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
        key = (float(energy), float(pixel_size))
        if key in self.transmission_cache:
            return self.transmission_cache[key] # To not repeat the calculation

        wavelength = 1.23984193 / (1000 * energy)  # µm
        k = 2.0 * np.pi / wavelength  # 1/µm

        refr_index_term = self.set_refr_index(energy)
        proj = self.make_geometry(self.n, pixel_size)

        refractive_index_projection = proj * refr_index_term
        transmission = np.exp(-1j * k * refractive_index_projection)
        self.transmission_cache[key] = transmission
        return transmission

    def set_refr_index(self, energy):
        return make_material(self.material, energy)

    def make_geometry(self, n, pixel_size):
        raise NotImplementedError("Subclasses must implement make_geometry().")
        
class Sphere(GeometricObject):
    def __init__(self, n, inner_radius, outer_radius, pixel_size, material, DSO, x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)
        
        self.inner_radius = float(inner_radius)
        self.outer_radius = float(outer_radius)

    def make_geometry(self, n, pixel_size):
        x, y = self.grid(n, pixel_size)
        
        image = np.zeros((n,n), dtype=float)
        
        r2 = x**2 + y**2
        """
        R2 = self.outer_radius ** 2
        thickness = np.zeros((n, n), dtype=float)
        inside = r2 < R2
        thickness[inside] = 2.0 * np.sqrt(np.maximum(R2 - r2[inside], 0.0))"""
        
        mask_ext = r2 < self.outer_radius**2

        if self.inner_radius == 0.:
            # Solid Sphere
            image[mask_ext] = 2.0*np.sqrt(self.outer_radius**2 - r2[mask_ext])
        else:
            "Hollow Sphere"
            mask_int = r2 < self.inner_radius**2
            mask_hollow = mask_ext & mask_int

            # Outer region
            image[mask_ext] = 2.0*np.sqrt(self.outer_radius**2 - r2[mask_ext])

            # Substract inner hollow region
            image[mask_hollow] -= 2.0*np.sqrt(self.inner_radius**2 - r2[mask_hollow])

            # Ensure no negative thickness
            image[image < 0 ] = 0
        
        return image
       
class Wedge(GeometricObject):
    def __init__(self, n, width, thickness, pixel_size, material, DSO, x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)
        
        self.width = width
        self.thickness = thickness
        
    def make_geometry(self, n, pixel_size):
        width = self.width
        thickness = self.thickness
        x, y = self.grid(n, pixel_size)
        
        image = np.zeros((n,n))

        half_width = width / 2
        wedge_mask = np.abs(x) < half_width
        image[wedge_mask] = ((half_width-np.abs(x[wedge_mask])) / half_width) * thickness
        
        return image
        
               
class Cylinder(GeometricObject):
    def __init__(self, n, outer_radius, inner_radius,Orientation,pixel_size, material, DSO, x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)
  
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.Orientation = Orientation

    def make_geometry(self, n, pixel_size):
        outer_radius = self.outer_radius
        inner_radius = self.inner_radius
        Orientation = self.Orientation
        
        x, y = self.grid(n, pixel_size)
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
    def __init__(self, n, period, DC, pixel_size, material, DSO, thickness_um=None, grating_type='custom', angle = 0,x_shift=0, y_shift=0, step =0, design_energy=None):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)

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

        x_shift_px = round(self.x_shift / pixel_size)
        y_shift_px = round(self.y_shift / pixel_size)
        if x_shift_px:
            mask = np.roll(mask, x_shift_px, axis=1)
        if y_shift_px:
            mask = np.roll(mask, y_shift_px, axis=0)

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
        """Set the grating displacement in physical micrometres."""
        self.step = new_step
        self.transmission_cache.clear()
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

    def __init__(self, n, slit_width, center_distance, screen_thickness, pixel_size, material, DSO, slit_height=None,x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)
        self.slit_width = slit_width
        self.center_distance = center_distance
        self.screen_thickness = screen_thickness
        self.slit_height = None if slit_height is None else slit_height

    def make_geometry(self, n, pixel_size):
        x, y = self.grid(n, pixel_size)

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

    def __init__(self, n, pixel_size, material, DSO, orientation='vertical', blocked_side='left', screen_thickness=50.0, edge_offset_um=0.0, x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)
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
        x, y = self.grid(n, pixel_size)

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
    
    
class Disk(GeometricObject):
    def __init__(self, n, radius, thickness, pixel_size, material, DSO, x_shift=0, y_shift=0):
        super().__init__(n, pixel_size, material, DSO, x_shift=x_shift, y_shift=y_shift)

        self.radius = float(radius)
        self.thickness = float(thickness)

    def make_geometry(self, n, pixel_size):
        x, y = self.grid(n, pixel_size)

        r2 = x**2 + y**2

        image = np.zeros((n, n), dtype=float)
        mask = r2 < self.radius**2

        image[mask] = self.thickness

        return image


class CT_phantom(GeometricObject):
    """
    Circular CT phantom with a background material and circular inserts.
    """

    def __init__(self, n, radius, thickness, pixel_size, background_material,
        inserts=None, DSO=0, center=(0.0, 0.0), x_shift=0, y_shift=0,):
        
        super().__init__(n, pixel_size, background_material, DSO, x_shift=x_shift, y_shift=y_shift)

        self.radius = float(radius)
        self.thickness = float(thickness)
        self.center = (float(center[0]), float(center[1]))
        self.background_material = background_material
        self.inserts = [] if inserts is None else list(inserts)

        self.projection = self.make_geometry(self.n, self.pixel_size_init)

    def _insert_mask(self, x, y, insert, outer_mask):
        radius = float(insert.get('radius', 0.0))
        if radius <= 0:
            raise ValueError("Each insert must have a positive radius.")

        center = insert.get('center', (0.0, 0.0))
        center_x = float(center[0])
        center_y = float(center[1])
        return ((x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2) & outer_mask

    def make_geometry(self, n, pixel_size):
        x, y = self.grid(n, pixel_size, center=self.center)

        thickness_map = np.zeros((n, n), dtype=float)
        outer_mask = (x**2 + y**2) <= self.radius**2
        thickness_map[outer_mask] = self.thickness

        occupied_inserts = np.zeros((n, n), dtype=bool)
        for insert in self.inserts:
            insert_mask = self._insert_mask(x, y, insert, outer_mask)
            if np.any(insert_mask & occupied_inserts):
                raise ValueError("Insert disks cannot overlap inside CT_phantom.")

            insert_thickness = float(insert.get('thickness', self.thickness))
            thickness_map[insert_mask] = insert_thickness
            occupied_inserts |= insert_mask

        return thickness_map

    def transmission_function(self, energy, pixel_size):
        wavelength = 1.23984193 / (1000 * energy)  # µm
        k = 2.0 * np.pi / wavelength  # 1/µm

        x, y = self.grid(self.n, pixel_size, center=self.center)
        outer_mask = (x**2 + y**2) <= self.radius**2

        phase_projection = np.zeros((self.n, self.n), dtype=np.complex128)
        base_refr_index = make_material(self.background_material, energy)
        phase_projection[outer_mask] = self.thickness * base_refr_index

        occupied_inserts = np.zeros((self.n, self.n), dtype=bool)
        for insert in self.inserts:
            insert_mask = self._insert_mask(x, y, insert, outer_mask)
            if np.any(insert_mask & occupied_inserts):
                raise ValueError("Insert disks cannot overlap inside CT_phantom.")

            insert_material = insert.get('material', self.background_material)
            insert_refr_index = make_material(insert_material, energy)
            insert_thickness = float(insert.get('thickness', self.thickness))
            phase_projection[insert_mask] = insert_thickness * insert_refr_index
            occupied_inserts |= insert_mask

        return np.exp(-1j * k * phase_projection)

    def get_thickness_map(self):
        return self.projection

    def get_background_material(self):
        return self.background_material

    def get_inserts(self):
        return list(self.inserts)

