import numpy as np
from skimage.transform import resize
from scipy.ndimage import rotate, shift
import json

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
    def __init__(self, n, radius, pixel_size, delta, beta, center=(0.0, 0.0)):
        super().__init__(n, pixel_size, delta, beta)
        self.radius = radius
        self.center = center

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        image = np.zeros((n, n))
        r2 = x**2 + y**2
        mask = r2 < radius**2
        image[mask] = 2 * np.sqrt(radius**2 - r2[mask])
        self.projection = image
                
class Background(GeometricObject):
    def __init__(self, n,pixel_size, delta,beta):
        super().__init__(n, pixel_size,delta,beta)
        self.projection = np.ones((n,n))*beta

class Cylinder(GeometricObject):
    def __init__(self, n, outer_radius, pixel_size, delta, beta, Orientation='Vertical', inner_radius=0, center=(0.0, 0.0), angle_deg=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.Orientation = Orientation
        self.center = center
        self.angle_deg = angle_deg

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        theta = np.deg2rad(angle_deg)
        xr = np.cos(theta) * x + np.sin(theta) * y
        yr = -np.sin(theta) * x + np.cos(theta) * y

        image = np.zeros((n, n))
        if Orientation == 'Vertical':
            r_sq = xr**2
        elif Orientation == 'Horizontal':
            r_sq = yr**2
        else:
            raise ValueError("Orientation must be 'Vertical' or 'Horizontal'.")

        mask_ext = r_sq < outer_radius**2

        if inner_radius == 0.:
            image[mask_ext] = 2 * np.sqrt(outer_radius**2 - r_sq[mask_ext])
        else:
            mask_int = r_sq < inner_radius**2
            mask_hollow = mask_ext & mask_int
            image[mask_ext] = 2 * np.sqrt(outer_radius**2 - r_sq[mask_ext])
            image[mask_hollow] -= 2 * np.sqrt(inner_radius**2 - r_sq[mask_hollow])
            image[image < 0] = 0

        self.projection = image
         

class Wedge(GeometricObject):
    def __init__(self, n, width, thickness, pixel_size, delta, beta, center=(0.0, 0.0), angle_deg=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.width = width
        self.thickness = thickness
        self.center = center
        self.angle_deg = angle_deg

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        theta = np.deg2rad(angle_deg)
        xr = np.cos(theta) * x + np.sin(theta) * y
        yr = -np.sin(theta) * x + np.cos(theta) * y

        half_width = width / 2
        half_thickness = thickness / 2
        image = np.zeros((n, n))
        mask = (np.abs(xr) < half_width) & (np.abs(yr) < half_thickness)
        image[mask] = half_width - np.abs(xr[mask])
        self.projection = image


class Ellipsoid(GeometricObject):
    def __init__(self, n, radius_x, radius_y, radius_z, pixel_size, delta, beta, center=(0.0, 0.0), angle_deg=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.radius_z = radius_z
        self.center = center
        self.angle_deg = angle_deg

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        theta = np.deg2rad(angle_deg)
        xr = np.cos(theta) * x + np.sin(theta) * y
        yr = -np.sin(theta) * x + np.cos(theta) * y

        image = np.zeros((n, n))
        ellipsoid_norm = (xr / radius_x) ** 2 + (yr / radius_y) ** 2
        mask = ellipsoid_norm < 1
        image[mask] = 2 * radius_z * np.sqrt(1 - ellipsoid_norm[mask])
        self.projection = image


class Rectangle(GeometricObject):
    def __init__(self, n, width, height, thickness, pixel_size, delta, beta, center=(0.0, 0.0), angle_deg=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.width = width
        self.height = height
        self.thickness = thickness
        self.center = center
        self.angle_deg = angle_deg

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        theta = np.deg2rad(angle_deg)
        xr = np.cos(theta) * x + np.sin(theta) * y
        yr = -np.sin(theta) * x + np.cos(theta) * y

        image = np.zeros((n, n))
        mask = (np.abs(xr) <= width / 2) & (np.abs(yr) <= height / 2)
        image[mask] = thickness
        self.projection = image


class GaussianLens(GeometricObject):
    def __init__(self, n, sigma_x, sigma_y, peak_thickness, pixel_size, delta, beta, center=(0.0, 0.0), angle_deg=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.sigma_x = sigma_x
        self.sigma_y = sigma_y
        self.peak_thickness = peak_thickness
        self.center = center
        self.angle_deg = angle_deg

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        theta = np.deg2rad(angle_deg)
        xr = np.cos(theta) * x + np.sin(theta) * y
        yr = -np.sin(theta) * x + np.cos(theta) * y

        self.projection = peak_thickness * np.exp(-(xr**2 / (2 * sigma_x**2) + yr**2 / (2 * sigma_y**2)))


class SinusoidalGrating(GeometricObject):
    def __init__(self, n, period, mean_thickness, modulation, pixel_size, delta, beta, axis='x', phase=0.0):
        super().__init__(n, pixel_size, delta, beta)
        self.period = period
        self.mean_thickness = mean_thickness
        self.modulation = modulation
        self.axis = axis
        self.phase = phase

        y, x = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size
        y = (y + 0.5) * pixel_size

        if axis == 'x':
            carrier = x
        elif axis == 'y':
            carrier = y
        else:
            raise ValueError("axis must be 'x' or 'y'.")

        image = mean_thickness * (1 + modulation * np.sin(2 * np.pi * carrier / period + phase))
        image[image < 0] = 0
        self.projection = image
        
        
class Disk(GeometricObject):
    def __init__(self, n, radius, pixel_size, delta, beta, center=(0.0, 0.0)):
        super().__init__(n, pixel_size, delta, beta)
        self.radius = radius
        self.center = center

        x, y = np.mgrid[(-n-0)//2:(n-0)//2, (-n-0)//2:(n-0)//2]
        x = (x + 0.5) * pixel_size - center[0]
        y = (y + 0.5) * pixel_size - center[1]

        r2 = x**2 + y**2
        image = np.zeros((n, n))
        mask = r2 < radius**2
        image[mask] = 2 * radius
        self.projection = image


class GeometryManager(GeometricObject):
    def __init__(self, n, pixel_size, delta, beta):
        super().__init__(n, pixel_size, delta, beta)
        self.layers = []
        self.projection = np.zeros((n, n), dtype=float)

    def _transform_projection(self, projection, shift_x=0.0, shift_y=0.0, angle_deg=0.0, order=1):
        rotated = rotate(
            projection,
            angle=angle_deg,
            reshape=False,
            order=order,
            mode='constant',
            cval=0.0,
            prefilter=False,
        )

        shift_pixels = (shift_y / self.pixel_size, shift_x / self.pixel_size)
        transformed = shift(
            rotated,
            shift=shift_pixels,
            order=order,
            mode='constant',
            cval=0.0,
            prefilter=False,
        )
        return transformed

    def add_object(self, obj, shift_x=0.0, shift_y=0.0, angle_deg=0.0, scale=1.0, mode='add'):
        projection = np.array(obj.Obtain_projection(), dtype=float)
        transformed = self._transform_projection(projection, shift_x=shift_x, shift_y=shift_y, angle_deg=angle_deg)
        transformed *= scale

        if mode == 'add':
            self.projection += transformed
        elif mode == 'subtract':
            self.projection -= transformed
#         elif mode == 'max':
#             self.projection = np.maximum(self.projection, transformed)
        else:
            raise ValueError("mode must be 'add' or 'subtract'.")

        self.projection[self.projection < 0] = 0
        self.layers.append(
            {
                'type': obj.__class__.__name__,
                'shift_x': shift_x,
                'shift_y': shift_y,
                'angle_deg': angle_deg,
                'scale': scale,
                'mode': mode,
            }
        )

    def add_cylinder_bundle(self, outer_radius, inner_radii, inner_offsets, orientation='Vertical'):
        if len(inner_radii) != len(inner_offsets):
            raise ValueError("inner_radii and inner_offsets must have the same length.")

        outer = Cylinder(
            n=self.n,
            outer_radius=outer_radius,
            pixel_size=self.pixel_size,
            delta=self.delta,
            beta=self.beta,
            Orientation=orientation,
            inner_radius=0,
        )
        self.add_object(outer, mode='add')

        for radius, (dx, dy) in zip(inner_radii, inner_offsets):
            inner = Cylinder(
                n=self.n,
                outer_radius=radius,
                pixel_size=self.pixel_size,
                delta=self.delta,
                beta=self.beta,
                Orientation=orientation,
                inner_radius=0,
            )
            self.add_object(inner, shift_x=dx, shift_y=dy, mode='subtract')

    def clear(self):
        self.projection = np.zeros((self.n, self.n), dtype=float)
        self.layers = []


class MultiMaterialComposite(GeometricObject):
    """
    Class to generate multple material Composite object.
    """
    def __init__(self, n, pixel_size, thickness_map, phase_map, attenuation_map):
        super().__init__(n=n, pixel_size=pixel_size, delta=1.0, beta=1.0)
        self.projection = np.asarray(thickness_map, dtype=float)
        self.phase_map = np.asarray(phase_map, dtype=float)
        self.attenuation_map = np.asarray(attenuation_map, dtype=float)

        expected = (n, n)
        if self.projection.shape != expected:
            raise ValueError(f"thickness_map must have shape {expected}.")
        if self.phase_map.shape != expected:
            raise ValueError(f"phase_map must have shape {expected}.")
        if self.attenuation_map.shape != expected:
            raise ValueError(f"attenuation_map must have shape {expected}.")

    def Obtain_Phase_Gradient(self, axis):
        return np.gradient(self.phase_map, self.pixel_size, axis=axis)

    def a0_Distribution(self):
        return np.exp(-2 * self.attenuation_map)

    def Obtain_Phase_Distribuction(self):
        return self.phase_map

    def Obtain_Phase_Laplacian(self):
        phase_gradient_axis0 = np.gradient(self.phase_map, self.pixel_size, axis=0)
        phase_gradient_axis1 = np.gradient(self.phase_map, self.pixel_size, axis=1)
        phase_gradient2_axis0 = np.gradient(phase_gradient_axis0, self.pixel_size, axis=0)
        phase_gradient2_axis1 = np.gradient(phase_gradient_axis1, self.pixel_size, axis=1)
        laplacian_phase = phase_gradient2_axis0 + phase_gradient2_axis1
        return -laplacian_phase

    def get_thickness_map(self):
        return self.projection

    def get_phase_map(self):
        return self.phase_map

    def get_attenuation_map(self):
        return self.attenuation_map

    def get_transmission_map(self):
        return self.a0_Distribution()


class GeometryFactory:
    _OBJECT_REGISTRY = {
        'sphere': Sphere,
        'cylinder': Cylinder,
        'wedge': Wedge,
        'ellipsoid': Ellipsoid,
        'rectangle': Rectangle,
        'sinusoidal_grating': SinusoidalGrating,
        'disk': Disk,
    }

    @classmethod
    def available_geometries(cls):
        return sorted(cls._OBJECT_REGISTRY.keys())

    @classmethod
    def create_object(cls, geometry_type, n, pixel_size, delta, beta, **params):
        key = geometry_type.lower()
        if key not in cls._OBJECT_REGISTRY:
            supported = ', '.join(cls.available_geometries())
            raise ValueError(f"Unknown geometry '{geometry_type}'. Supported geometries: {supported}")

        object_class = cls._OBJECT_REGISTRY[key]
        if 'orientation' in params and 'Orientation' not in params:
            params['Orientation'] = params.pop('orientation')

        return object_class(
            n=n,
            pixel_size=pixel_size,
            delta=delta,
            beta=beta,
            **params,
        )

    @classmethod
    def create_manager_from_config(cls, config, n, pixel_size, delta, beta):
        manager = GeometryManager(n=n, pixel_size=pixel_size, delta=delta, beta=beta)

        for entry in config.get('objects', []):
            geometry_type = entry['type']
            params = entry.get('params', {})
            transform = entry.get('transform', {})

            obj = cls.create_object(
                geometry_type=geometry_type,
                n=n,
                pixel_size=pixel_size,
                delta=delta,
                beta=beta,
                **params,
            )

            manager.add_object(
                obj,
                shift_x=transform.get('shift_x', 0.0),
                shift_y=transform.get('shift_y', 0.0),
                angle_deg=transform.get('angle_deg', 0.0),
                scale=entry.get('scale', 1.0),
                mode=entry.get('mode', 'add'),
            )

        for bundle in config.get('cylinder_bundles', []):
            manager.add_cylinder_bundle(outer_radius=bundle['outer_radius'], inner_radii=bundle.get('inner_radii', []),
                inner_offsets=bundle.get('inner_offsets', []), orientation=bundle.get('orientation', 'Vertical'))

        return manager

    @classmethod
    def load_config_json(cls, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def create_manager_from_json(cls, json_path, n, pixel_size, delta, beta):
        config = cls.load_config_json(json_path)
        return cls.create_manager_from_config(config=config, n=n, pixel_size=pixel_size,
            delta=delta, beta=beta)


class RandomSimGenerator:
    def __init__(self, n, pixel_size, material_library, seed=None, object_count_range=(1, 4),
        allow_inserts=True, insert_probability=0.5, max_inserts_per_object=2, energy_keV=20.0):
        self.n = int(n)
        self.pixel_size = float(pixel_size)
        self.material_library = list(material_library)
        self.rng = np.random.default_rng(seed)
        self.object_count_range = object_count_range
        self.allow_inserts = bool(allow_inserts)
        self.insert_probability = float(insert_probability)
        self.max_inserts_per_object = int(max_inserts_per_object)
        self.shape_types = ['sphere', 'cylinder', 'rectangle', 'ellipsoid', 'wedge', 'disk']

        if not self.material_library:
            raise ValueError("material_library cannot be empty.")

        wavelength = 1.23984193 / (1000.0 * float(energy_keV))  # µm
        self._k = 2.0 * np.pi / wavelength
    

    def _sample_material(self):
        material = self.material_library[int(self.rng.integers(0, len(self.material_library)))]
        delta = float(material['delta'])
        beta  = float(material['beta'])
        delta *= self._k
        beta *= self._k
        return delta, beta

    def _sample_center(self):
        fov_um = self.n * self.pixel_size
        limit = 0.3 * fov_um
        cx = float(self.rng.uniform(-limit, limit))
        cy = float(self.rng.uniform(-limit, limit))
        return (cx, cy)

    def _sample_object(self, delta, beta):
        fov_um = self.n * self.pixel_size
        shape = self.shape_types[int(self.rng.integers(0, len(self.shape_types)))]
        center = self._sample_center()
        angle_deg = float(self.rng.uniform(0.0, 180.0))

        if shape == 'sphere':
            radius = float(self.rng.uniform(0.04, 0.6) * fov_um)
            return Sphere(self.n, radius, self.pixel_size, delta, beta, center=center)

        if shape == 'cylinder':
            outer_radius = float(self.rng.uniform(0.03, 0.6) * fov_um)
            if self.rng.random() < 0.35:
                inner_radius = float(self.rng.uniform(0.2, 0.7) * outer_radius)
            else:
                inner_radius = 0.0
            orientation = 'Vertical' if self.rng.random() < 0.5 else 'Horizontal'
            return Cylinder(self.n, outer_radius, self.pixel_size, delta, beta,
                Orientation=orientation, inner_radius=inner_radius, center=center, angle_deg=angle_deg)

        if shape == 'rectangle':
            width = float(self.rng.uniform(0.05, 0.50) * fov_um)
            height = float(self.rng.uniform(0.05, 0.50) * fov_um)
            thickness = float(self.rng.uniform(0.02, 0.8) * fov_um)
            return Rectangle(self.n, width, height, thickness, self.pixel_size, delta, beta, center=center, angle_deg=angle_deg)

        if shape == 'ellipsoid':
            rx = float(self.rng.uniform(0.04, 0.3) * fov_um)
            ry = float(self.rng.uniform(0.04, 0.3) * fov_um)
            rz = float(self.rng.uniform(0.02, 0.3) * fov_um)
            return Ellipsoid(self.n, rx, ry, rz, self.pixel_size, delta, beta, center=center, angle_deg=angle_deg)

        if shape == 'disk':
            radius = float(self.rng.uniform(0.04, 0.6) * fov_um)
            return Disk(self.n, radius, self.pixel_size, delta, beta, center=center)

        if shape == 'wedge':
            width = float(self.rng.uniform(0.08, 0.35) * fov_um)
            thickness = float(self.rng.uniform(0.03, 0.18) * fov_um)
            return Wedge(self.n, width, thickness, self.pixel_size, delta, beta, center=center, angle_deg=angle_deg)

    def _compose_with_inserts(self, base_obj, base_delta, base_beta):
        base_proj = np.asarray(base_obj.Obtain_projection(), dtype=float)
        base_proj = np.clip(base_proj, 0.0, None)
        local_phase = base_proj * base_delta
        local_atten = base_proj * base_beta

        if not self.allow_inserts or self.rng.random() > self.insert_probability:
            return base_proj, local_phase, local_atten

        insert_count = int(self.rng.integers(1, self.max_inserts_per_object + 1))
        remaining_base = base_proj.copy()

        for _ in range(insert_count):
            ins_delta, ins_beta = self._sample_material()
            ins_obj = self._sample_object(ins_delta, ins_beta)
            ins_proj = np.asarray(ins_obj.Obtain_projection(), dtype=float)
            ins_proj = np.clip(ins_proj, 0.0, None)
            replaced = np.minimum(remaining_base, ins_proj)
            if not np.any(replaced):
                continue
            local_phase += replaced * (ins_delta - base_delta)
            local_atten += replaced * (ins_beta - base_beta)
            remaining_base -= replaced

        return base_proj, local_phase, local_atten

    def generate(self, object_count=None):
        if object_count is None:
            low, high = self.object_count_range
            object_count = int(self.rng.integers(low, high + 1))

        thickness_map = np.zeros((self.n, self.n), dtype=float)
        phase_map = np.zeros((self.n, self.n), dtype=float)
        attenuation_map = np.zeros((self.n, self.n), dtype=float)

        for _ in range(object_count):
            base_delta, base_beta = self._sample_material()
            base_obj = self._sample_object(base_delta, base_beta)
            base_thickness, local_phase, local_atten = self._compose_with_inserts(base_obj, base_delta, base_beta)
            thickness_map += base_thickness
            phase_map += local_phase
            attenuation_map += local_atten

        return MultiMaterialComposite(n=self.n, pixel_size=self.pixel_size, thickness_map=thickness_map,
            phase_map=phase_map, attenuation_map=attenuation_map)
