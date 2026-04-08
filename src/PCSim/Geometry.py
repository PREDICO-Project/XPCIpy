class Geometry():
    def __init__(self, DSD=None):

        #self.DG0G1 = DG0G1
        #self.DG1G2 = DG1G2 
        #self.DSD = self.distance_Source_Detector()
        #self.Magnification = self.calculate_magnification()
        #self.DOD = DG1G2
        self.DSD = DSD
        
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
        mean_wavelength = 1.23984193/(mean_energy*1000)
        DSG1 = TL_CONFIG.DSG1
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
        
        if Source.Beam_distribution == 'Plane': 
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

