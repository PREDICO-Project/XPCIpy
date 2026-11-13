import numpy as np
import os


def Simulation(Object, Phase_Steps, noise_mean, error_steps_mean, error_dose_mean,
    Moire=False, axis=1, dark_field_map=None, moire_fringes_count=10, moire_profile='linear',
    moire_direction='x', moire_phase_scale=1.0, moire_phase_offset=0.0, log_path=None):
    '''
    Create the Curve Intensity Modulation for a given Object, Background and Grating.
    I(x,y,k)= exp(-error_Dose)*[a_0(x,y)+a_1(x,y)*cos(Phi(x,y)+2*pi*k/M+error_steps)] + noise
    k: k-th Phase Step
    M: Total Phase Steps
    '''
    n = Object.n
    #Final_Images = []
    #Final_Images_reference = []
    Images =np.zeros((Phase_Steps,n,n))
    Images_reference =np.zeros((Phase_Steps,n,n))  
    a0 = Object.a0_Distribution()
    Phase = Object.Obtain_Phase_Distribuction()
    Diff_Phase = Object.Obtain_Phase_Gradient(axis = axis)

    if dark_field_map is None:
        visibility = np.ones((n, n), dtype=float)
    else:
        visibility = np.asarray(dark_field_map, dtype=float)
        if visibility.shape != (n, n):
            raise ValueError("dark_field_map must have shape (n, n).")
        visibility = np.clip(visibility, 0.0, 1.0)

    a1 = (a0 / 2) * visibility
    if log_path:
        try:
            os.remove(log_path)
        except Exception:
            pass
        with open(log_path, 'a', encoding='utf-8') as file:
            file.write('lambda lambda_reference phase_step phase_step_reference\n')
    if Moire:
        number_fringes = int(moire_fringes_count)
        yy, xx = np.meshgrid(np.arange(n, dtype=float), np.arange(n, dtype=float), indexing='ij')

        direction = str(moire_direction).strip().lower()
        if direction == 'y':
            coord = yy / max(1.0, (n - 1.0))
        elif direction == 'diag':
            coord = (xx + yy) / max(1.0, 2.0 * (n - 1.0))
        else:
            coord = xx / max(1.0, (n - 1.0))

        base_phase = 2.0 * np.pi * float(number_fringes) * coord + float(moire_phase_offset)
        profile = str(moire_profile).strip().lower()
        scale = float(moire_phase_scale)

        if profile == 'sinusoidal':
            moire_fringes = scale * np.sin(base_phase)
        elif profile == 'triangular':
            moire_fringes = scale * (2.0 / np.pi) * np.arcsin(np.sin(base_phase))
        elif profile == 'square':
            moire_fringes = scale * np.sign(np.sin(base_phase))
        else:
            # Backward-compatible default used previously: a linear phase ramp.
            moire_fringes = scale * base_phase
    else:
        moire_fringes = np.zeros((n,n))
    for i,phase_step in enumerate(range(Phase_Steps)):
        lambda_k_1 = np.random.normal(0,error_dose_mean)
        lambda_k_2 = np.random.normal(0,error_dose_mean)
        phase_step_error = np.random.normal(0,error_steps_mean)
        phase_step_error_r = np.random.normal(0,error_steps_mean)
        if log_path:
            with open(log_path, 'a', encoding='utf-8') as file:
                file.write(f'{lambda_k_1:.5g} {lambda_k_2:.5g} {phase_step_error:.5g} {phase_step_error_r:.5g}\n')
        
        noise1 = np.random.normal(0,noise_mean, (n,n))
        noise2 = np.random.normal(0,noise_mean, (n,n))
        Images[phase_step, :,:] = np.exp(lambda_k_1)*(a0+a1*np.cos(Diff_Phase+2*np.pi*phase_step/Phase_Steps+phase_step_error+moire_fringes))+noise1
        Images_reference[phase_step,:,:] =np.exp(lambda_k_2)*(1+0.5*np.cos(2*np.pi*phase_step/Phase_Steps+phase_step_error_r+moire_fringes))+noise2
        
    #Images += noise1
    #Images_reference += noise2
    return Images, Images_reference


def simulate_random_tl_sample(generator, phase_steps, noise_mean, error_steps_mean, error_dose_mean,
    axis=1, moire=False, dark_field_map=None, moire_fringes_count=10, moire_profile='linear', moire_direction='x',
    moire_phase_scale=1.0, moire_phase_offset=0.0, log_path=None):

    scene = generator.generate()
    phase_map = scene.get_phase_map()
    attenuation_map = scene.get_attenuation_map()
    transmission_map = scene.get_transmission_map()
    thickness_map = scene.get_thickness_map()
    phase_gradient = scene.Obtain_Phase_Gradient(axis=axis)
    phase_laplacian = scene.Obtain_Phase_Laplacian()

    images, images_reference = Simulation(scene, phase_steps, noise_mean, error_steps_mean, error_dose_mean,
        Moire=moire, axis=axis, dark_field_map=dark_field_map, moire_fringes_count=moire_fringes_count,
        moire_profile=moire_profile, moire_direction=moire_direction, moire_phase_scale=moire_phase_scale, moire_phase_offset=moire_phase_offset,
        log_path=log_path)

    return {
        'scene': scene,
        'thickness_map': thickness_map,
        'phase_map': phase_map,
        'attenuation_map': attenuation_map,
        'transmission_map': transmission_map,
        'phase_gradient': phase_gradient,
        'phase_laplacian': phase_laplacian,
        'images': np.asarray(images),
        'images_reference': np.asarray(images_reference),
    }


