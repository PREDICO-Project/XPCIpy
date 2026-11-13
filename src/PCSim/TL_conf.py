class TL_CONFIG():
    def __init__(self,Design_energy = None, G1_Period = None, G2_Period = None, DSG1 = None, DSD = None, DOD =None, Movable_Grating= None,G1_type= None, 
                 TL_multiple= None, Number_steps= None, Step_length= None, pixel_size= None, angle = 0, resolution = 0, pixel_detector=0):
        self.Design_energy = Design_energy # Energy of design (keV). It is the energy to calculate the Talbot_Distance
        self.G1_Period = G1_Period # Period of G1 in um
        self.G2_Period = G2_Period # Period of G2 in um
        self.DSG1 = DSG1 # Distance Source-G1 in cm
        self.DSD = DSD # Distance Object-Detector in cm
        self.Movable_Grating = Movable_Grating # Which grating is moving along the perpendicular direction
        self.G1_type = G1_type # Phase introduced by G1. It can be 'phase_pi', 'phase_pi_2'.
        self.TL_multiple = TL_multiple # Which fractional Talbot Distance between G1 and G2
        self.Number_steps = Number_steps # Number of steps
        self.Step_length = Step_length # Physical grating displacement per step (um)
        self.pixel_size = pixel_size # Pixel Size in um
        self.angle = angle # Angle between gratings
        self.resolution = resolution # Resolution of the detector in um
        self.pixel_detector = pixel_detector # Detector's pixel size in um

    