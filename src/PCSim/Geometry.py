class Geometry():
    def __init__(self, DSD=None):

        #self.DG0G1 = DG0G1
        #self.DG1G2 = DG1G2 
        #self.DSD = self.distance_Source_Detector()
        #self.Magnification = self.calculate_magnification()
        #self.DOD = DG1G2
        self.DSD = DSD

    @staticmethod
    def energy_to_wavelength_um(energy_keV):
        if energy_keV <= 0:
            raise ValueError("energy_keV must be > 0.")
        return 1.23984193 / (energy_keV * 1000)

    @staticmethod
    def wavelength_to_energy_keV(wavelength_um):
        if wavelength_um <= 0:
            raise ValueError("wavelength_um must be > 0.")
        return 1.23984193 / (wavelength_um * 1000)
        
    def distance_Source_Detector(self):
        return self.DG0G1+self.DG1G2
    

    def period_G0_image(self, p0, eta):
        return p0*self.Magnification/(self.Magnification-1)/eta
    
    def period_G1_image(self, p1, eta):
        return p1*self.Magnification/eta
    
    def calculate_Talbot_distance_and_G2period(self,Source, TL_CONFIG):
        Period_G1 = TL_CONFIG.G1_Period
        Talbot_multiple = TL_CONFIG.TL_multiple
        mean_energy = Source.mean_energy
        mean_wavelength = self.energy_to_wavelength_um(mean_energy)
        DSG1 = TL_CONFIG.DSG1
        distance = None
        G2Period = None
        if Source.Beam_distribution == 'Conical':
            if TL_CONFIG.G1_type == 'phase_pi':
            #distance_Talbot = Period_G1**2/(2*mean_wavelength)*10**(-4) #pi/2
                distance_Talbot = Period_G1**2/(8*mean_wavelength)*10**(-4)
                distance = DSG1*Talbot_multiple*distance_Talbot/(DSG1-Talbot_multiple*distance_Talbot)
                M = (DSG1+distance)/DSG1
                G2Period =Period_G1*M/2 # pi
            if TL_CONFIG.G1_type == 'phase_pi_2':
                distance_Talbot = Period_G1**2/(2*mean_wavelength)*10**(-4) #pi/2
                distance = DSG1*Talbot_multiple*distance_Talbot/(DSG1-Talbot_multiple*distance_Talbot)
                M = (DSG1+distance)/DSG1
                G2Period =Period_G1*M # pi/2

            print('Talbot distance (cm): '+str(distance_Talbot))
            print('G2 period: '+ str(G2Period))
            print('The magnification is: ' +str(M))
        
        elif Source.Beam_distribution == 'Plane': 
            M =1
            if TL_CONFIG.G1_type == 'phase_pi':
                G2Period = Period_G1/2
                distance = Period_G1**2/(8*mean_wavelength)*10**(-4)
            if TL_CONFIG.G1_type == 'phase_pi_2':
                G2Period = Period_G1
                distance = Period_G1**2/(2*mean_wavelength)*10**(-4)
            print('Talbot distance (cm): '+str(distance))
            print('G2 period: '+ str(G2Period))
            print('The magnification is: ' +str(M))  
        else:
            raise ValueError(f"Unsupported Beam_distribution: {Source.Beam_distribution}")
        return distance, G2Period

    def calculate_magnification(self, distance_1, distance_2, conical):
        # distance1 and distance2 are measured from same point
        if not conical:
            return 1
        if distance_1 <= 0:
            raise ValueError("distance_1 must be > 0 for conical magnification.")
        
        return distance_2/distance_1

    def pixel_size_at_distance(self, original_px, distance_1, distance_2, conical):

        return original_px * self.calculate_magnification(distance_1, distance_2, conical)
    
    
    def calculate_Fresnel_number(self, distance, pixel_size, energy):
        # energy in keV, distance in cm, pixel_size in um
        if distance <= 0:
            raise ValueError("distance must be > 0.")
        if pixel_size <= 0:
            raise ValueError("pixel_size must be > 0.")
        wavelength = self.energy_to_wavelength_um(energy)
        return pixel_size**2/(wavelength*distance*10**(4))

    def calculate_geometric_blur(self, source_size, distance_source_object, distance_object_detector, conical=True):
        # Returns penumbra blur in um at detector plane due to finite source size.
        return source_size * (distance_object_detector / distance_source_object)

